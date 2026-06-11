import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../features/auth/auth.dart';
import '../features/scan/scan.dart';

final apiClientProvider = Provider<SapiSehatApiClient>((ref) => SapiSehatApiClient());
final sessionStoreProvider = Provider<SessionStore>((ref) => MemorySessionStore());

final sessionControllerProvider = StateNotifierProvider<SessionController, AccountSession?>((ref) {
  return SessionController(ref.read(sessionStoreProvider));
});

class SessionController extends StateNotifier<AccountSession?> {
  SessionController(this.store) : super(null);
  final SessionStore store;

  Future<void> save(AccountSession session) async {
    await store.save(session);
    state = session;
  }

  Future<void> clear() async {
    await store.clear();
    state = null;
  }
}

final localHistoryProvider = StateNotifierProvider<LocalHistoryController, List<ScanResult>>((ref) => LocalHistoryController());

class LocalHistoryController extends StateNotifier<List<ScanResult>> {
  LocalHistoryController() : super(const []);
  void add(ScanResult result) => state = [result, ...state];
}
