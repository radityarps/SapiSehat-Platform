class FarmerPreferences {
  const FarmerPreferences({
    required this.farmerId,
    this.scanResultNotifications = true,
    this.syncNotifications = true,
    this.areaRiskAdvisoryNotifications = false,
    this.followUpStatusNotifications = true,
    this.quietHoursEnabled = false,
    this.quietHoursStart = '21:00',
    this.quietHoursEnd = '06:00',
  });

  final String farmerId;
  final bool scanResultNotifications;
  final bool syncNotifications;
  final bool areaRiskAdvisoryNotifications;
  final bool followUpStatusNotifications;
  final bool quietHoursEnabled;
  final String quietHoursStart;
  final String quietHoursEnd;

  factory FarmerPreferences.fromJson(Map<String, dynamic> json) => FarmerPreferences(
        farmerId: json['farmer_id'] as String,
        scanResultNotifications: json['scan_result_notifications'] as bool? ?? true,
        syncNotifications: json['sync_notifications'] as bool? ?? true,
        areaRiskAdvisoryNotifications: json['area_risk_advisory_notifications'] as bool? ?? false,
        followUpStatusNotifications: json['follow_up_status_notifications'] as bool? ?? true,
        quietHoursEnabled: json['quiet_hours_enabled'] as bool? ?? false,
        quietHoursStart: json['quiet_hours_start'] as String? ?? '21:00',
        quietHoursEnd: json['quiet_hours_end'] as String? ?? '06:00',
      );

  Map<String, dynamic> toJson() => {
        'scan_result_notifications': scanResultNotifications,
        'sync_notifications': syncNotifications,
        'area_risk_advisory_notifications': areaRiskAdvisoryNotifications,
        'follow_up_status_notifications': followUpStatusNotifications,
        'quiet_hours_enabled': quietHoursEnabled,
        'quiet_hours_start': quietHoursStart,
        'quiet_hours_end': quietHoursEnd,
      };

  FarmerPreferences copyWith({
    bool? scanResultNotifications,
    bool? syncNotifications,
    bool? areaRiskAdvisoryNotifications,
    bool? followUpStatusNotifications,
    bool? quietHoursEnabled,
  }) => FarmerPreferences(
        farmerId: farmerId,
        scanResultNotifications: scanResultNotifications ?? this.scanResultNotifications,
        syncNotifications: syncNotifications ?? this.syncNotifications,
        areaRiskAdvisoryNotifications: areaRiskAdvisoryNotifications ?? this.areaRiskAdvisoryNotifications,
        followUpStatusNotifications: followUpStatusNotifications ?? this.followUpStatusNotifications,
        quietHoursEnabled: quietHoursEnabled ?? this.quietHoursEnabled,
        quietHoursStart: quietHoursStart,
        quietHoursEnd: quietHoursEnd,
      );
}
