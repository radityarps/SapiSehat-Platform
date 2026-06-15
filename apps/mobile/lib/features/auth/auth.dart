class AccountSession {
  AccountSession({
    required this.token,
    required this.farmerId,
    required this.email,
    this.name = '',
    this.address,
    this.jurisdictionId = 'tembalang',
    this.isActive = true,
  });

  final String token;
  final String farmerId;
  final String email;
  final String name;
  final String? address;
  final String jurisdictionId;
  final bool isActive;

  AccountSession copyWith({
    String? name,
    String? address,
    String? jurisdictionId,
    bool? isActive,
  }) => AccountSession(
    token: token,
    farmerId: farmerId,
    email: email,
    name: name ?? this.name,
    address: address ?? this.address,
    jurisdictionId: jurisdictionId ?? this.jurisdictionId,
    isActive: isActive ?? this.isActive,
  );
}

class FarmerRegistrationDraft {
  FarmerRegistrationDraft({
    required this.name,
    required this.email,
    required this.password,
    required this.jurisdictionId,
  });
  final String name;
  final String email;
  final String password;
  final String jurisdictionId;

  Map<String, dynamic> toJson() => {
    'name': name,
    'email': email,
    'password': password,
    'jurisdiction_id': jurisdictionId,
  };
}

class FarmerProfileDraft {
  FarmerProfileDraft({
    required this.name,
    required this.jurisdictionId,
    this.address,
  });
  final String name;
  final String jurisdictionId;
  final String? address;
  Map<String, dynamic> toJson() => {
    'name': name,
    'jurisdiction_id': jurisdictionId,
    if (address != null) 'address': address,
  };
}

abstract class SessionStore {
  Future<void> save(AccountSession session);
  Future<AccountSession?> load();
  Future<void> clear();
}

class MemorySessionStore implements SessionStore {
  AccountSession? _session;
  String? get token => _session?.token;

  @override
  Future<AccountSession?> load() async => _session;

  @override
  Future<void> save(AccountSession session) async => _session = session;

  @override
  Future<void> clear() async => _session = null;
}
