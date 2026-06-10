class CattleProfile {
  CattleProfile({required this.id, required this.tag, required this.status});
  final String id;
  final String tag;
  final String status;
  factory CattleProfile.fromJson(Map<String, dynamic> json) => CattleProfile(
        id: json['id'] as String,
        tag: json['tag'] as String,
        status: (json['status'] ?? 'active') as String,
      );
}

class CattleDraft {
  CattleDraft({required this.tag, this.sex = 'female', this.breed = 'unknown', this.ageMonths = 24, this.status = 'active', this.jurisdictionId = 'tembalang'});
  final String tag;
  final String sex;
  final String breed;
  final int ageMonths;
  final String status;
  final String jurisdictionId;
  Map<String, dynamic> toJson() => {'tag': tag, 'sex': sex, 'breed': breed, 'age_months': ageMonths, 'status': status, 'jurisdiction_id': jurisdictionId};
}
