import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../features/auth/auth.dart';
import '../features/auth/login_screen.dart';
import '../features/cattle/cattle_screen.dart';
import '../features/guide/guide_screen.dart';
import '../features/history/history_screen.dart';
import '../features/onboarding/onboarding_screen.dart';
import '../features/scan/scan_screen.dart';
import '../features/settings/settings_screen.dart';
import 'providers.dart';
import 'theme.dart';

class SapiSehatApp extends StatelessWidget {
  const SapiSehatApp({
    super.key,
    this.apiClient,
    this.sessionStore,
    this.initialSession,
  });
  final SapiSehatApiClient? apiClient;
  final SessionStore? sessionStore;
  final AccountSession? initialSession;

  @override
  Widget build(BuildContext context) {
    final store = sessionStore ?? FileSessionStore();
    final overrides = <Override>[
      if (apiClient != null) apiClientProvider.overrideWithValue(apiClient!),
      sessionStoreProvider.overrideWithValue(store),
      if (initialSession != null)
        sessionControllerProvider.overrideWith(
          (ref) => SessionController(store, initialSession),
        ),
    ];
    return ProviderScope(
      overrides: overrides,
      child: const _SapiSehatAppView(),
    );
  }
}

class _SapiSehatAppView extends ConsumerStatefulWidget {
  const _SapiSehatAppView();
  @override
  ConsumerState<_SapiSehatAppView> createState() => _SapiSehatAppViewState();
}

class _SapiSehatAppViewState extends ConsumerState<_SapiSehatAppView> {
  bool onboarded = false;

  @override
  void initState() {
    super.initState();
    _checkStoredSession();
  }

  Future<void> _checkStoredSession() async {
    final current = ref.read(sessionControllerProvider);
    if (current != null) return;
    final store = ref.read(sessionStoreProvider);
    final saved = await store.load();
    if (saved != null && mounted) {
      ref.read(sessionControllerProvider.notifier).restore(saved);
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionControllerProvider);
    final apiClient = ref.watch(apiClientProvider);
    final sessionStore = ref.watch(sessionStoreProvider);

    final isAuthed = session != null;

    return MaterialApp(
      title: 'SapiSehat',
      theme: sapiSehatTheme(),
      home: isAuthed
          ? HomeScreen(
              apiClient: apiClient,
              session: session,
              sessionStore: sessionStore,
            )
          : !onboarded
          ? OnboardingScreen(onFinished: () => setState(() => onboarded = true))
          : LoginScreen(
              apiClient: apiClient,
              sessionStore: sessionStore,
              onLoggedIn: (value) =>
                  ref.read(sessionControllerProvider.notifier).save(value),
            ),
    );
  }
}

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({
    super.key,
    required this.apiClient,
    required this.session,
    required this.sessionStore,
  });
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final SessionStore sessionStore;

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  var tab = 0;

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionControllerProvider) ?? widget.session;
    final pages = [
      CattleScreen(apiClient: widget.apiClient, session: session),
      ScanScreen(
        apiClient: widget.apiClient,
        session: session,
        onScan: (result) => ref.read(localHistoryProvider.notifier).add(result),
      ),
      HistoryScreen(
        apiClient: widget.apiClient,
        session: session,
        localHistory: ref.watch(localHistoryProvider),
        onUpdateLocal: (result) =>
            ref.read(localHistoryProvider.notifier).update(result),
        onDeleteLocal: (result) =>
            ref.read(localHistoryProvider.notifier).remove(result),
      ),
      GuideScreen(apiClient: widget.apiClient, session: session),
      SettingsScreen(
        apiClient: widget.apiClient,
        session: session,
        sessionStore: widget.sessionStore,
        onSessionChanged: (s) =>
            ref.read(sessionControllerProvider.notifier).save(s),
        onArchived: () => ref.read(sessionControllerProvider.notifier).clear(),
        onLogout: () => ref.read(sessionControllerProvider.notifier).clear(),
      ),
    ];
    return Scaffold(
      appBar: AppBar(toolbarHeight: 0),
      body: pages[tab],
      bottomNavigationBar: NavigationBar(
        selectedIndex: tab,
        onDestinationSelected: (value) => setState(() => tab = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.pets), label: 'Sapi'),
          NavigationDestination(icon: Icon(Icons.camera_alt), label: 'Scan'),
          NavigationDestination(icon: Icon(Icons.history), label: 'Riwayat'),
          NavigationDestination(icon: Icon(Icons.menu_book), label: 'Panduan'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'Setelan'),
        ],
      ),
    );
  }
}
