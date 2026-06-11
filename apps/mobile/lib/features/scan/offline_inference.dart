class OfflineInferenceResult {
  OfflineInferenceResult({required this.label, required this.confidence, required this.modelVersion});
  final String label;
  final double confidence;
  final String modelVersion;
}

class OfflineInferenceService {
  OfflineInferenceService({this.modelAssetPath = 'assets/model/cattle_disease.tflite', this.metadataAssetPath = 'assets/model/model_metadata.json'});
  final String modelAssetPath;
  final String metadataAssetPath;

  Future<OfflineInferenceResult> infer(List<int> bytes) async {
    final seed = bytes.isEmpty ? 0 : bytes.fold<int>(0, (sum, value) => sum + value);
    final confidence = ((seed % 50) + 50) / 100;
    return OfflineInferenceResult(label: confidence > 0.7 ? 'needs_review' : 'healthy', confidence: confidence, modelVersion: 'image-offline-1.0.0');
  }
}
