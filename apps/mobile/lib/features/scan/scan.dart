const activeDetectionClasses = <String>{'FMD', 'healthy'};

abstract class ScanDisplayResult {
  String get localId;
  String? get cattleId;
  String get label;
  double get confidence;
  DateTime get capturedAt;
  String get inferenceMode;
  String get syncStatus;
  String? get imagePath;
  String get modelVersion;
  Map<String, double> get scores;

  ScanDisplayResult copyWith({String? cattleId, bool clearCattleId = false});
}

class HistoricalScanResult implements ScanDisplayResult {
  HistoricalScanResult({
    required this.localId,
    this.cattleId,
    required this.label,
    required this.confidence,
    required this.capturedAt,
    required this.inferenceMode,
    this.imagePath,
  });

  @override
  final String localId;
  @override
  final String? cattleId;
  @override
  final String label;
  @override
  final double confidence;
  @override
  final DateTime capturedAt;
  @override
  final String inferenceMode;
  @override
  final String? imagePath;
  @override
  final String modelVersion = 'historical';
  @override
  final Map<String, double> scores = const {};
  @override
  String get syncStatus => 'synced';

  @override
  HistoricalScanResult copyWith({
    String? cattleId,
    bool clearCattleId = false,
  }) => HistoricalScanResult(
    localId: localId,
    cattleId: clearCattleId ? null : cattleId ?? this.cattleId,
    label: label,
    confidence: confidence,
    capturedAt: capturedAt,
    inferenceMode: inferenceMode,
    imagePath: imagePath,
  );
}

class ScanResult implements ScanDisplayResult {
  static ScanResult fromInference({
    required String localId,
    String? cattleId,
    required String label,
    required double confidence,
    required DateTime capturedAt,
    required String inferenceMode,
    required String syncStatus,
    String? imagePath,
    required String modelVersion,
    required Map<String, double> scores,
  }) => ScanResult(
    localId: localId,
    cattleId: cattleId,
    label: label,
    confidence: confidence,
    capturedAt: capturedAt,
    inferenceMode: inferenceMode,
    syncStatus: syncStatus,
    imagePath: imagePath,
    modelVersion: modelVersion,
    scores: scores,
  );
  ScanResult({
    required this.localId,
    this.cattleId,
    required this.label,
    required this.confidence,
    required this.capturedAt,
    required this.inferenceMode,
    required this.syncStatus,
    this.imagePath,
    required this.modelVersion,
    required this.scores,
  }) {
    if (!activeDetectionClasses.contains(label)) {
      throw ArgumentError.value(label, 'label', 'must be FMD or healthy');
    }
    if (!confidence.isFinite || confidence < 0 || confidence > 1) {
      throw ArgumentError.value(confidence, 'confidence');
    }
    if (modelVersion.isEmpty) {
      throw ArgumentError.value(modelVersion, 'modelVersion');
    }
    if (scores.length != activeDetectionClasses.length ||
        !scores.keys.toSet().containsAll(activeDetectionClasses) ||
        scores.values.any(
          (score) => !score.isFinite || score < 0 || score > 1,
        ) ||
        (scores.values.reduce((a, b) => a + b) - 1).abs() >= 0.001 ||
        (scores[label]! - confidence).abs() >= 0.001) {
      throw ArgumentError.value(
        scores,
        'scores',
        'must contain active probabilities summing to one',
      );
    }
  }
  @override
  final String localId;
  @override
  final String? cattleId;
  @override
  final String label;
  @override
  final double confidence;
  @override
  final DateTime capturedAt;
  @override
  final String inferenceMode;
  @override
  final String syncStatus;
  @override
  final String? imagePath;
  @override
  final String modelVersion;
  @override
  final Map<String, double> scores;

  @override
  ScanResult copyWith({String? cattleId, bool clearCattleId = false}) =>
      ScanResult(
        localId: localId,
        cattleId: clearCattleId ? null : cattleId ?? this.cattleId,
        label: label,
        confidence: confidence,
        capturedAt: capturedAt,
        inferenceMode: inferenceMode,
        syncStatus: syncStatus,
        imagePath: imagePath,
        modelVersion: modelVersion,
        scores: Map<String, double>.from(scores),
      );
}

class PendingOfflineDetection {
  PendingOfflineDetection({
    required this.localId,
    required this.farmerId,
    this.cattleId,
    required this.localCreatedAt,
    required this.label,
    required this.confidence,
    required this.modelVersion,
    required this.scores,
  }) {
    if (!activeDetectionClasses.contains(label)) {
      throw ArgumentError.value(label, 'label', 'must be FMD or healthy');
    }
    if (modelVersion.isEmpty) {
      throw ArgumentError.value(modelVersion, 'modelVersion');
    }
    if (scores.length != activeDetectionClasses.length ||
        !scores.keys.toSet().containsAll(activeDetectionClasses) ||
        scores.values.any(
          (score) => !score.isFinite || score < 0 || score > 1,
        ) ||
        (scores.values.reduce((a, b) => a + b) - 1).abs() >= 0.001 ||
        (scores[label]! - confidence).abs() >= 0.001) {
      throw ArgumentError.value(
        scores,
        'scores',
        'must contain active probabilities summing to one',
      );
    }
  }
  final String localId;
  final String farmerId;
  final String? cattleId;
  final DateTime localCreatedAt;
  final String label;
  final double confidence;
  final String modelVersion;
  final Map<String, double> scores;

  Map<String, dynamic> toSyncJson() => {
    'local_detection_id': localId,
    'farmer_id': farmerId,
    'cattle_id': cattleId,
    'local_created_at': localCreatedAt.toIso8601String(),
    'image_evidence': {
      'source': 'image',
      'model_version': modelVersion,
      'inference_mode': 'offline',
      'disease_scores': scores,
      'top_class': label,
      'confidence': confidence,
      'quality_status': 'accepted',
      'rejection_reasons': [],
    },
    'nlp_evidence': null,
    'offline_fused_result': {'disease_class': label, 'confidence': confidence},
  };
}
