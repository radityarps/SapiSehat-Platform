class FarmerPreferences {
  const FarmerPreferences({
    required this.farmerId,
    this.scanResultNotifications = true,
    this.syncNotifications = true,
    this.areaRiskAdvisoryNotifications = false,
    this.followUpStatusNotifications = true,
  });

  final String farmerId;
  final bool scanResultNotifications;
  final bool syncNotifications;
  final bool areaRiskAdvisoryNotifications;
  final bool followUpStatusNotifications;

  factory FarmerPreferences.fromJson(Map<String, dynamic> json) =>
      FarmerPreferences(
        farmerId: json['farmer_id'] as String,
        scanResultNotifications:
            json['scan_result_notifications'] as bool? ?? true,
        syncNotifications: json['sync_notifications'] as bool? ?? true,
        areaRiskAdvisoryNotifications:
            json['area_risk_advisory_notifications'] as bool? ?? false,
        followUpStatusNotifications:
            json['follow_up_status_notifications'] as bool? ?? true,
      );

  Map<String, dynamic> toJson() => {
    'scan_result_notifications': scanResultNotifications,
    'sync_notifications': syncNotifications,
    'area_risk_advisory_notifications': areaRiskAdvisoryNotifications,
    'follow_up_status_notifications': followUpStatusNotifications,
  };

  FarmerPreferences copyWith({
    bool? scanResultNotifications,
    bool? syncNotifications,
    bool? areaRiskAdvisoryNotifications,
    bool? followUpStatusNotifications,
  }) => FarmerPreferences(
    farmerId: farmerId,
    scanResultNotifications:
        scanResultNotifications ?? this.scanResultNotifications,
    syncNotifications: syncNotifications ?? this.syncNotifications,
    areaRiskAdvisoryNotifications:
        areaRiskAdvisoryNotifications ?? this.areaRiskAdvisoryNotifications,
    followUpStatusNotifications:
        followUpStatusNotifications ?? this.followUpStatusNotifications,
  );
}
