import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:image/image.dart' as image_lib;
import 'package:tflite_flutter/tflite_flutter.dart';

const activeModelClassOrder = <String>['FMD', 'healthy', 'non_cattle'];
const modelInputSize = 224;
const modelResizeInterpolation = image_lib.Interpolation.linear;

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
    if (modelVersion is! String ||
        modelVersion.isEmpty ||
        classOrder == null ||
        !_sameClassOrder(classOrder) ||
        inputSize?.length != 2 ||
        inputSize![0] != modelInputSize ||
        inputSize[1] != modelInputSize ||
        preprocessing['channels'] != 3 ||
        preprocessing['color_mode'] != 'RGB' ||
        inputRange is! List ||
        inputRange.length != 2 ||
        inputRange[0] != 0 ||
        inputRange[1] != 255 ||
        internalRescaling != true ||
        json['verification'] is! Map ||
        (json['verification'] as Map)['overall_pass'] != true) {
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
    this.modelAssetPath = 'assets/model/cattle_disease.tflite',
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
        metadata.classOrder[i]: _round4(probabilities[i]),
    };
    final label = metadata.classOrder[topIndex];
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
        outputs.first.shape.join(',') != '1,${activeModelClassOrder.length}' ||
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
    value.length == activeModelClassOrder.length &&
    value.asMap().entries.every(
      (entry) => entry.value == activeModelClassOrder[entry.key],
    );
