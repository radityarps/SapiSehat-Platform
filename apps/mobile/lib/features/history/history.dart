const activeHistoryClasses = {'FMD', 'healthy'};

class DetectionHistoryItem {
  DetectionHistoryItem({required this.id, required this.farmerId, this.cattleId, required this.label, required this.confidence, required this.inferenceMode, required this.createdAt});
  final String id;
  final String farmerId;
  final String? cattleId;
  final String label;
  final double confidence;
  final String inferenceMode;
  final DateTime? createdAt;
  String get safeSummary => 'Risk signal: $label';
  factory DetectionHistoryItem.fromJson(Map<String, dynamic> json) {
    final label = (json['disease_class'] ?? json['result_label']) as String?;
    if (label == null || !activeHistoryClasses.contains(label)) {
      throw const FormatException('History contains an inactive disease class');
    }
    return DetectionHistoryItem(
        id: json['id'] as String,
        farmerId: json['farmer_id'] as String,
        cattleId: json['cattle_id'] as String?,
        label: (json['disease_class'] ?? json['result_label'] ?? 'needs_review') as String,
        confidence: ((json['confidence'] ?? 0.0) as num).toDouble(),
        inferenceMode: (json['inference_mode'] ?? 'online') as String,
        createdAt: json['created_at'] == null ? null : DateTime.tryParse(json['created_at'] as String),
      );
  }
}
