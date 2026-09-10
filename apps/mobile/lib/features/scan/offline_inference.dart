import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:image/image.dart' as image_lib;
import 'package:tflite_flutter/tflite_flutter.dart';

const rawModelClassOrder = <String>['non_sapi', 'pmk', 'sehat'];
const rawModelClassIndices = <String, String>{
  '0': 'non_sapi',
  '1': 'pmk',
  '2': 'sehat',
};
const modelLabelMapping = <String, String>{
  'non_sapi': 'non_cattle',
  'pmk': 'FMD',
  'sehat': 'healthy',
};
const requiredVerificationGates = <String>[
  'metadata_pair_contract',
  'metadata_activation_status',
  'artifact_checksums',
  'tensor_contract_declaration',
  'runtime_tensor_contract',
  'finite_probability_contract',
  'valid_image_top_class_parity',
  'score_tolerance',
  'labeled_corpus_expectations',
  'corpus_label_provenance',
  'corpus_file_integrity',
  'corrupt_input_fixture',
  'former_lsd_policy',
  'class_identity_provenance',
  'corpus_source_permissions',
];
const modelInputSize = 224;
const modelResizeInterpolation = image_lib.Interpolation.linear;
const _qualitySampleSize = 512;
const _minimumBlurScore = 100.0;
const _minimumBrightness = 40.0;

class ImageQualityException implements Exception {
  const ImageQualityException(this.reasons);
  final List<String> reasons;

  String get message => reasons.join('\n');

  @override
  String toString() => message;
}

class DetectionUnavailableException implements Exception {
  const DetectionUnavailableException(this.message);
  final String message;

  @override
  String toString() => message;
}

void validateImageQuality(List<int> bytes) {
  final decoded = image_lib.decodeImage(Uint8List.fromList(bytes));
  if (decoded == null) {
    throw const ImageQualityException(['Gambar tidak dapat dibaca.']);
  }
  final reasons = <String>[];
  if (decoded.width < modelInputSize || decoded.height < modelInputSize) {
    reasons.add('Resolusi gambar terlalu kecil (minimal 224 × 224 piksel).');
  }
  final scale = decoded.width > decoded.height
      ? _qualitySampleSize / decoded.width
      : _qualitySampleSize / decoded.height;
  final sample = scale < 1
      ? image_lib.copyResize(
          decoded,
          width: (decoded.width * scale).round(),
          height: (decoded.height * scale).round(),
          interpolation: image_lib.Interpolation.linear,
        )
      : decoded;
  final luminance = List<double>.filled(sample.width * sample.height, 0);
  var luminanceTotal = 0.0;
  for (var y = 0; y < sample.height; y++) {
    for (var x = 0; x < sample.width; x++) {
      final pixel = sample.getPixel(x, y);
      final value = 0.299 * pixel.r + 0.587 * pixel.g + 0.114 * pixel.b;
      luminance[y * sample.width + x] = value;
      luminanceTotal += value;
    }
  }
  if (luminanceTotal / luminance.length < _minimumBrightness) {
    reasons.add('Gambar terlalu gelap. Gunakan pencahayaan yang lebih terang.');
  }
  var sum = 0.0;
  var sumSquared = 0.0;
  var count = 0;
  for (var y = 1; y < sample.height - 1; y++) {
    for (var x = 1; x < sample.width - 1; x++) {
      final index = y * sample.width + x;
      final laplacian =
          luminance[index - sample.width] +
          luminance[index - 1] +
          luminance[index + 1] +
          luminance[index + sample.width] -
          4 * luminance[index];
      sum += laplacian;
      sumSquared += laplacian * laplacian;
      count++;
    }
  }
  final blurScore = count == 0
      ? 0.0
      : sumSquared / count - (sum / count) * (sum / count);
  if (blurScore < _minimumBlurScore) {
    reasons.add('Gambar terlalu buram. Stabilkan kamera dan ambil ulang.');
  }
  if (reasons.isNotEmpty) throw ImageQualityException(reasons);
}

class NonCattleImageException implements Exception {
  const NonCattleImageException(this.message);
  final String message;

  @override
  String toString() => message;
}

class OfflineInferenceResult {
  OfflineInferenceResult({
    required this.label,
    required this.confidence,
    required this.modelVersion,
    required this.scores,
  });

  final String label;
  final double confidence;
  final String modelVersion;
  final Map<String, double> scores;
}

@visibleForTesting
class OfflineModelMetadata {
  const OfflineModelMetadata({
    required this.modelVersion,
    required this.classOrder,
    required this.inputSize,
  });

  final String modelVersion;
  final List<String> classOrder;
  final int inputSize;

  factory OfflineModelMetadata.fromJson(Map<String, dynamic> json) {
    final preprocessing = json['preprocessing'] as Map<String, dynamic>? ?? {};
    final inputSize = preprocessing['input_size'] as List<dynamic>?;
    final modelVersion = json['model_version'];
    final classOrder = (json['class_order'] as List<dynamic>?)
        ?.map((value) => value.toString())
        .toList();
    final inputRange = preprocessing['input_range'];
    final internalRescaling = preprocessing['internal_rescaling'];
    final classIndices = json['class_indices'];
    final tensorContract = json['tensor_contract'];
    final verification = json['verification'];
    final requiredGates = verification is Map
        ? verification['required_gates']
        : null;
    final verificationGates = verification is Map
        ? verification['gates']
        : null;
    if (modelVersion is! String ||
        modelVersion.trim().isEmpty ||
        json['base_model_version'] is! String ||
        (json['base_model_version'] as String).trim().isEmpty ||
        json['architecture'] is! String ||
        (json['architecture'] as String).trim().isEmpty ||
        json['asset'] != 'pmk_fp32.tflite' ||
        json['sha256'] is! String ||
        (json['sha256'] as String).trim().isEmpty ||
        json['artifact_status'] != 'verified' ||
        classOrder == null ||
        !_sameClassOrder(classOrder) ||
        classIndices is! Map ||
        !_sameClassIndices(classIndices) ||
        json['label_mapping'] is! Map ||
        !_sameLabelMapping(json['label_mapping'] as Map) ||
        tensorContract is! Map ||
        !_validTensorContract(tensorContract) ||
        inputSize?.length != 2 ||
        inputSize![0] != modelInputSize ||
        inputSize[1] != modelInputSize ||
        preprocessing['channels'] != 3 ||
        preprocessing['color_mode'] != 'RGB' ||
        preprocessing['resize_method'] != 'bilinear' ||
        inputRange is! List ||
        inputRange.length != 2 ||
        inputRange[0] != 0 ||
        inputRange[1] != 255 ||
        preprocessing['input_dtype'] != 'float32' ||
        internalRescaling != true ||
        preprocessing['internal_rescaling_scale'] != 1 / 127.5 ||
        preprocessing['internal_rescaling_offset'] != -1.0 ||
        verification is! Map ||
        verification['report'] is! String ||
        (verification['report'] as String).trim().isEmpty ||
        verification['corpus_manifest'] is! String ||
        (verification['corpus_manifest'] as String).trim().isEmpty ||
        verification['overall_pass'] != true ||
        verification['activation_ready'] != true ||
        verification['artifact_status'] != 'verified' ||
        requiredGates is! List ||
        requiredGates.length != requiredVerificationGates.length ||
        requiredGates.any((gate) => gate is! String) ||
        verificationGates is! Map ||
        !_allVerificationGatesPass(requiredGates, verificationGates)) {
      throw const FormatException(
        'Offline model metadata is missing a verified three-output contract',
      );
    }
    return OfflineModelMetadata(
      modelVersion: modelVersion,
      classOrder: classOrder,
      inputSize: modelInputSize,
    );
  }
}

class OfflineInferenceService {
  OfflineInferenceService({
    this.modelAssetPath = 'assets/model/pmk_fp32.tflite',
    this.metadataAssetPath = 'assets/model/model_metadata.json',
    @visibleForTesting Future<List<double>> Function(List<int> bytes)? runModel,
    @visibleForTesting OfflineModelMetadata? metadata,
  }) : _runModelForTest = runModel,
       _metadataForTest = metadata;

  final String modelAssetPath;
  final String metadataAssetPath;
  final Future<List<double>> Function(List<int> bytes)? _runModelForTest;
  final OfflineModelMetadata? _metadataForTest;

  Interpreter? _interpreter;
  OfflineModelMetadata? _metadata;

  Future<OfflineInferenceResult> infer(List<int> bytes) async {
    final metadata = await _loadMetadata();
    final rawScores = _runModelForTest == null
        ? await _runTflite(bytes, metadata)
        : await _runModelForTest(bytes);
    if (rawScores.length != metadata.classOrder.length) {
      throw StateError(
        'Offline model returned ${rawScores.length} scores for '
        '${metadata.classOrder.length} classes',
      );
    }
    final probabilities = _asProbabilities(rawScores);
    final topIndex = _argMax(probabilities);
    final scores = <String, double>{
      for (var i = 0; i < metadata.classOrder.length; i++)
        modelLabelMapping[metadata.classOrder[i]]!: _round4(probabilities[i]),
    };
    final label = modelLabelMapping[metadata.classOrder[topIndex]]!;
    if (label == 'non_cattle') {
      throw const NonCattleImageException(
        'Gambar ditolak karena bukan gambar sapi.',
      );
    }
    final activeTotal = scores['FMD']! + scores['healthy']!;
    if (activeTotal <= 0) {
      throw const FormatException(
        'Offline model probabilities must have positive active mass',
      );
    }
    final activeScores = {
      'FMD': scores['FMD']! / activeTotal,
      'healthy': scores['healthy']! / activeTotal,
    };
    return OfflineInferenceResult(
      label: label,
      confidence: activeScores[label]!,
      modelVersion: metadata.modelVersion,
      scores: activeScores,
    );
  }

  Future<void> dispose() async {
    _interpreter?.close();
    _interpreter = null;
  }

  Future<OfflineModelMetadata> _loadMetadata() async {
    if (_metadataForTest != null) return _metadataForTest;
    final cached = _metadata;
    if (cached != null) return cached;
    final raw = await rootBundle.loadString(metadataAssetPath);
    final metadata = OfflineModelMetadata.fromJson(
      jsonDecode(raw) as Map<String, dynamic>,
    );
    _metadata = metadata;
    return metadata;
  }

  Future<List<double>> _runTflite(
    List<int> bytes,
    OfflineModelMetadata metadata,
  ) async {
    final interpreter = await _loadInterpreter(metadata);
    final input = _preprocess(bytes, metadata.inputSize);
    final output = [List<double>.filled(metadata.classOrder.length, 0)];
    interpreter.run(input, output);
    return output.first;
  }

  Future<Interpreter> _loadInterpreter(OfflineModelMetadata metadata) async {
    final cached = _interpreter;
    if (cached != null) return cached;
    final interpreter = await Interpreter.fromAsset(modelAssetPath);
    interpreter.allocateTensors();
    final inputs = interpreter.getInputTensors();
    final outputs = interpreter.getOutputTensors();
    if (inputs.length != 1 ||
        outputs.length != 1 ||
        inputs.first.shape.length != 4 ||
        inputs.first.shape.join(',') != '1,$modelInputSize,$modelInputSize,3' ||
        outputs.first.shape.join(',') != '1,${rawModelClassOrder.length}' ||
        inputs.first.type != TensorType.float32 ||
        outputs.first.type != TensorType.float32 ||
        metadata.classOrder.length != outputs.first.shape.last) {
      interpreter.close();
      throw const FormatException('Offline TFLite tensor contract is invalid');
    }
    _interpreter = interpreter;
    return interpreter;
  }

  List<List<List<List<double>>>> _preprocess(List<int> bytes, int inputSize) {
    final decoded = image_lib.decodeImage(Uint8List.fromList(bytes));
    if (decoded == null) {
      throw const FormatException('Unsupported image bytes for offline model');
    }
    final oriented = image_lib.bakeOrientation(decoded);
    final resized = image_lib.copyResize(
      oriented,
      width: inputSize,
      height: inputSize,
      interpolation: modelResizeInterpolation,
    );
    return [
      List.generate(inputSize, (y) {
        return List.generate(inputSize, (x) {
          final pixel = resized.getPixel(x, y);
          return [pixel.r.toDouble(), pixel.g.toDouble(), pixel.b.toDouble()];
        });
      }),
    ];
  }

  List<double> _asProbabilities(List<double> values) {
    if (values.any((value) => value.isNaN || value.isInfinite) ||
        values.any((value) => value < 0 || value > 1)) {
      throw const FormatException(
        'Offline model returned invalid probabilities',
      );
    }
    final sum = values.fold<double>(0, (total, value) => total + value);
    if ((sum - 1.0).abs() >= 0.001) {
      throw const FormatException('Offline model probabilities must sum to 1');
    }
    return values;
  }

  int _argMax(List<double> values) {
    var bestIndex = 0;
    var bestValue = values.first;
    for (var i = 1; i < values.length; i++) {
      if (values[i] > bestValue) {
        bestIndex = i;
        bestValue = values[i];
      }
    }
    return bestIndex;
  }

  double _round4(double value) => (value * 10000).roundToDouble() / 10000;
}

bool _sameClassOrder(List<String> value) =>
    value.length == rawModelClassOrder.length &&
    value.asMap().entries.every(
      (entry) => entry.value == rawModelClassOrder[entry.key],
    );

bool _sameClassIndices(Map<dynamic, dynamic> value) =>
    value.length == rawModelClassIndices.length &&
    rawModelClassIndices.entries.every(
      (entry) => value[entry.key] == entry.value,
    );

bool _sameLabelMapping(Map<dynamic, dynamic> value) =>
    value.length == modelLabelMapping.length &&
    modelLabelMapping.entries.every((entry) => value[entry.key] == entry.value);

bool _validTensorContract(Map<dynamic, dynamic> value) =>
    value['input_tensor_count'] == 1 &&
    value['output_tensor_count'] == 1 &&
    _sameList(value['input_shape'], [1, modelInputSize, modelInputSize, 3]) &&
    _sameList(value['output_shape'], [1, rawModelClassOrder.length]) &&
    value['input_dtype'] == 'float32' &&
    value['output_dtype'] == 'float32';

bool _sameList(dynamic value, List<int> expected) =>
    value is List &&
    value.length == expected.length &&
    value.asMap().entries.every((entry) => entry.value == expected[entry.key]);

bool _allVerificationGatesPass(
  List<dynamic> requiredGates,
  Map<dynamic, dynamic> gates,
) => requiredGates.asMap().entries.every(
  (entry) =>
      entry.value == requiredVerificationGates[entry.key] &&
      gates[entry.value] == true,
);
