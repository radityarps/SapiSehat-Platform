class CattleProfile {
  CattleProfile({
    required this.id,
    required this.tag,
    required this.status,
    this.sex = 'female',
    this.breed = 'unknown',
    this.ageMonths,
    this.birthYearEstimate,
    this.jurisdictionId = 'tembalang',
    this.isArchived = false,
    this.name,
    this.color,
    this.weightKg,
    this.reproductiveStatus,
    this.isPregnant,
    this.lastCalvingDate,
    this.lastVaccinationDate,
    this.lastDewormingDate,
    this.healthNotes,
    this.purchaseDate,
    this.purchasePriceIdr,
    this.notes,
  });

  final String id;
  final String tag;
  final String status;
  final String sex;
  final String breed;
  final int? ageMonths;
  final int? birthYearEstimate;
  final String jurisdictionId;
  final bool isArchived;
  final String? name;
  final String? color;
  final double? weightKg;
  final String? reproductiveStatus;
  final bool? isPregnant;
  final String? lastCalvingDate;
  final String? lastVaccinationDate;
  final String? lastDewormingDate;
  final String? healthNotes;
  final String? purchaseDate;
  final int? purchasePriceIdr;
  final String? notes;

  CattleProfile copyWith({
    String? tag,
    String? status,
    String? sex,
    String? breed,
    int? ageMonths,
    int? birthYearEstimate,
    String? jurisdictionId,
    bool? isArchived,
    String? name,
    String? color,
    double? weightKg,
    String? reproductiveStatus,
    bool? isPregnant,
    String? lastCalvingDate,
    String? lastVaccinationDate,
    String? lastDewormingDate,
    String? healthNotes,
    String? purchaseDate,
    int? purchasePriceIdr,
    String? notes,
  }) => CattleProfile(
    id: id,
    tag: tag ?? this.tag,
    status: status ?? this.status,
    sex: sex ?? this.sex,
    breed: breed ?? this.breed,
    ageMonths: ageMonths ?? this.ageMonths,
    birthYearEstimate: birthYearEstimate ?? this.birthYearEstimate,
    jurisdictionId: jurisdictionId ?? this.jurisdictionId,
    isArchived: isArchived ?? this.isArchived,
    name: name ?? this.name,
    color: color ?? this.color,
    weightKg: weightKg ?? this.weightKg,
    reproductiveStatus: reproductiveStatus ?? this.reproductiveStatus,
    isPregnant: isPregnant ?? this.isPregnant,
    lastCalvingDate: lastCalvingDate ?? this.lastCalvingDate,
    lastVaccinationDate: lastVaccinationDate ?? this.lastVaccinationDate,
    lastDewormingDate: lastDewormingDate ?? this.lastDewormingDate,
    healthNotes: healthNotes ?? this.healthNotes,
    purchaseDate: purchaseDate ?? this.purchaseDate,
    purchasePriceIdr: purchasePriceIdr ?? this.purchasePriceIdr,
    notes: notes ?? this.notes,
  );

  factory CattleProfile.fromJson(Map<String, dynamic> json) => CattleProfile(
    id: json['id'] as String,
    tag: json['tag'] as String,
    status: (json['status'] ?? 'active') as String,
    sex: (json['sex'] ?? 'female') as String,
    breed: (json['breed'] ?? 'unknown') as String,
    ageMonths: json['age_months'] as int?,
    birthYearEstimate: json['birth_year_estimate'] as int?,
    jurisdictionId: (json['jurisdiction_id'] ?? 'tembalang') as String,
    isArchived: json['is_archived'] as bool? ?? false,
    name: json['name'] as String?,
    color: json['color'] as String?,
    weightKg: (json['weight_kg'] as num?)?.toDouble(),
    reproductiveStatus: json['reproductive_status'] as String?,
    isPregnant: json['is_pregnant'] as bool?,
    lastCalvingDate: json['last_calving_date'] as String?,
    lastVaccinationDate: json['last_vaccination_date'] as String?,
    lastDewormingDate: json['last_deworming_date'] as String?,
    healthNotes: json['health_notes'] as String?,
    purchaseDate: json['purchase_date'] as String?,
    purchasePriceIdr: json['purchase_price_idr'] as int?,
    notes: json['notes'] as String?,
  );
}

class CattleDraft {
  CattleDraft({
    required this.tag,
    this.sex = 'female',
    this.breed = 'unknown',
    this.ageMonths = 24,
    this.status = 'active',
    this.jurisdictionId = 'tembalang',
    this.name,
    this.color,
    this.weightKg,
    this.reproductiveStatus,
    this.isPregnant,
    this.lastCalvingDate,
    this.lastVaccinationDate,
    this.lastDewormingDate,
    this.healthNotes,
    this.purchaseDate,
    this.purchasePriceIdr,
    this.notes,
  });

  final String tag;
  final String sex;
  final String breed;
  final int ageMonths;
  final String status;
  final String jurisdictionId;
  final String? name;
  final String? color;
  final double? weightKg;
  final String? reproductiveStatus;
  final bool? isPregnant;
  final String? lastCalvingDate;
  final String? lastVaccinationDate;
  final String? lastDewormingDate;
  final String? healthNotes;
  final String? purchaseDate;
  final int? purchasePriceIdr;
  final String? notes;

  Map<String, dynamic> toJson() => {
    'tag': tag,
    'sex': sex,
    'breed': breed,
    'age_months': ageMonths,
    'status': status,
    'jurisdiction_id': jurisdictionId,
    'name': name,
    'color': color,
    'weight_kg': weightKg,
    'reproductive_status': reproductiveStatus,
    'is_pregnant': isPregnant,
    'last_calving_date': lastCalvingDate,
    'last_vaccination_date': lastVaccinationDate,
    'last_deworming_date': lastDewormingDate,
    'health_notes': healthNotes,
    'purchase_date': purchaseDate,
    'purchase_price_idr': purchasePriceIdr,
    'notes': notes,
  };
}
