import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:image/image.dart' as image_lib;
import 'package:tflite_flutter/tflite_flutter.dart';

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
    return OfflineModelMetadata(
      modelVersion: json['model_version'] as String? ?? 'image-offline-1.0.0',
      classOrder:
          (json['class_order'] as List<dynamic>?)
              ?.map((value) => value.toString())
              .toList() ??
          const ['FMD', 'LSD', 'healthy'],
      inputSize: inputSize == null || inputSize.isEmpty
          ? 224
          : (inputSize.first as num).toInt(),
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
    final confidence = probabilities[topIndex];
    final scores = <String, double>{
      for (var i = 0; i < metadata.classOrder.length; i++)
        metadata.classOrder[i]: _round4(probabilities[i]),
    };
    return OfflineInferenceResult(
      label: metadata.classOrder[topIndex],
      confidence: _round4(confidence),
      modelVersion: metadata.modelVersion,
      scores: scores,
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
    final interpreter = await _loadInterpreter();
    final input = _preprocess(bytes, metadata.inputSize);
    final output = [List<double>.filled(metadata.classOrder.length, 0)];
    interpreter.run(input, output);
    return output.first;
  }

  Future<Interpreter> _loadInterpreter() async {
    final cached = _interpreter;
    if (cached != null) return cached;
    final interpreter = await Interpreter.fromAsset(modelAssetPath);
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
      interpolation: image_lib.Interpolation.linear,
    );
    return [
      List.generate(inputSize, (y) {
        return List.generate(inputSize, (x) {
          final pixel = resized.getPixel(x, y);
          return [pixel.r / 255.0, pixel.g / 255.0, pixel.b / 255.0];
        });
      }),
    ];
  }

  List<double> _asProbabilities(List<double> values) {
    final sum = values.fold<double>(0, (total, value) => total + value);
    final alreadyProbabilities =
        values.every((value) => value >= 0) && (sum - 1.0).abs() < 0.001;
    if (alreadyProbabilities) return values;

    final maxValue = values.reduce(math.max);
    final expValues = values
        .map((value) => math.exp(value - maxValue))
        .toList();
    final expSum = expValues.fold<double>(0, (total, value) => total + value);
    return expValues.map((value) => value / expSum).toList();
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
