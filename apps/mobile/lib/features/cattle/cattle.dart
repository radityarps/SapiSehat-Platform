class CattleProfile {
  CattleProfile({required this.id, required this.tag, required this.status, this.sex = 'female', this.breed = 'unknown', this.ageMonths, this.jurisdictionId = 'tembalang', this.isArchived = false});
  final String id;
  final String tag;
  final String status;
  final String sex;
  final String breed;
  final int? ageMonths;
  final String jurisdictionId;
  final bool isArchived;

  CattleProfile copyWith({String? tag, String? status, String? sex, String? breed, int? ageMonths, String? jurisdictionId, bool? isArchived}) => CattleProfile(id: id, tag: tag ?? this.tag, status: status ?? this.status, sex: sex ?? this.sex, breed: breed ?? this.breed, ageMonths: ageMonths ?? this.ageMonths, jurisdictionId: jurisdictionId ?? this.jurisdictionId, isArchived: isArchived ?? this.isArchived);

  factory CattleProfile.fromJson(Map<String, dynamic> json) => CattleProfile(
        id: json['id'] as String,
        tag: json['tag'] as String,
        status: (json['status'] ?? 'active') as String,
        sex: (json['sex'] ?? 'female') as String,
        breed: (json['breed'] ?? 'unknown') as String,
        ageMonths: json['age_months'] as int?,
        jurisdictionId: (json['jurisdiction_id'] ?? 'tembalang') as String,
        isArchived: json['is_archived'] as bool? ?? false,
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
