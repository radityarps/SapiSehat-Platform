class AccountSession {
  AccountSession({required this.token, required this.farmerId, required this.email});
  final String token;
  final String farmerId;
  final String email;
}

abstract class SessionStore {
  Future<void> save(AccountSession session);
  Future<AccountSession?> load();
}

class MemorySessionStore implements SessionStore {
  AccountSession? _session;
  String? get token => _session?.token;

  @override
  Future<AccountSession?> load() async => _session;

  @override
  Future<void> save(AccountSession session) async => _session = session;
}
