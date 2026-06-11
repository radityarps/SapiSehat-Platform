class ScanResult {
  ScanResult({required this.localId, this.cattleId, required this.label, required this.confidence, required this.capturedAt, required this.inferenceMode, required this.syncStatus});
  final String localId;
  final String? cattleId;
  final String label;
  final double confidence;
  final DateTime capturedAt;
  final String inferenceMode;
  final String syncStatus;
}

class PendingOfflineDetection {
  PendingOfflineDetection({required this.localId, required this.farmerId, this.cattleId, required this.localCreatedAt, required this.label, required this.confidence});
  final String localId;
  final String farmerId;
  final String? cattleId;
  final DateTime localCreatedAt;
  final String label;
  final double confidence;
  Map<String, dynamic> toSyncJson() => {
        'local_detection_id': localId,
        'farmer_id': farmerId,
        'cattle_id': cattleId,
        'local_created_at': localCreatedAt.toIso8601String(),
        'image_evidence': {
          'source': 'image',
          'model_version': 'image-offline-1.0.0',
          'inference_mode': 'offline',
          'disease_scores': {'healthy': 0.2, 'FMD': confidence, 'LSD': 0.1},
          'top_class': label,
          'confidence': confidence,
          'quality_status': 'accepted',
          'rejection_reasons': [],
        },
        'nlp_evidence': {
          'source': 'nlp',
          'model_version': 'nlp-offline-1.0.0',
          'inference_mode': 'offline',
          'questionnaire_answers': {},
          'notes_present': false,
          'disease_scores': {'healthy': 0.2, 'FMD': confidence, 'LSD': 0.1},
          'top_class': label,
          'confidence': confidence,
          'evidence_terms': [],
        },
        'offline_fused_result': {'disease_class': label, 'confidence': confidence},
      };
}
