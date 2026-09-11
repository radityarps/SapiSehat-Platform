import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../features/auth/auth.dart';
import '../features/scan/scan.dart';

final apiClientProvider = Provider<SapiSehatApiClient>(
  (ref) => SapiSehatApiClient(),
);
final sessionStoreProvider = Provider<SessionStore>(
  (ref) => FileSessionStore(),
);

final sessionControllerProvider =
    StateNotifierProvider<SessionController, AccountSession?>((ref) {
      return SessionController(ref.read(sessionStoreProvider));
    });

class SessionController extends StateNotifier<AccountSession?> {
  SessionController(this.store, [AccountSession? initialSession])
      : super(initialSession);
  final SessionStore store;

  void restore(AccountSession session) {
    state = session;
  }

  Future<void> save(AccountSession session) async {
    await store.save(session);
    state = session;
  }

  Future<void> clear() async {
    await store.clear();
    state = null;
  }
}

final localHistoryProvider =
    StateNotifierProvider<LocalHistoryController, List<ScanResult>>(
      (ref) => LocalHistoryController(),
    );

class LocalHistoryController extends StateNotifier<List<ScanResult>> {
  LocalHistoryController() : super(const []);
  void add(ScanResult result) => state = [result, ...state];

  void update(ScanResult result) => state = state
      .map((item) => item.localId == result.localId ? result : item)
      .toList();
  void remove(ScanResult result) =>
      state = state.where((item) => item.localId != result.localId).toList();
}
