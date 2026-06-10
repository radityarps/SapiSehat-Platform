import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../features/auth/auth.dart';
import '../features/cattle/cattle.dart';
import '../features/history/history.dart';
import '../features/scan/scan.dart';
import 'providers.dart';
import 'theme.dart';

class SapiSehatApp extends StatelessWidget {
  const SapiSehatApp({super.key, this.apiClient, this.sessionStore});

  final SapiSehatApiClient? apiClient;
  final SessionStore? sessionStore;

  @override
  Widget build(BuildContext context) {
    final overrides = <Override>[
      if (apiClient != null) apiClientProvider.overrideWithValue(apiClient!),
      if (sessionStore != null) sessionStoreProvider.overrideWithValue(sessionStore!),
    ];
    return ProviderScope(overrides: overrides, child: const _SapiSehatAppView());
  }
}

class _SapiSehatAppView extends ConsumerWidget {
  const _SapiSehatAppView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionControllerProvider);
    final apiClient = ref.watch(apiClientProvider);
    final sessionStore = ref.watch(sessionStoreProvider);
    return MaterialApp(
      title: 'SapiSehat',
      theme: sapiSehatTheme(),
      home: session == null
          ? LoginScreen(
              apiClient: apiClient,
              sessionStore: sessionStore,
              onLoggedIn: (value) => ref.read(sessionControllerProvider.notifier).save(value),
            )
          : HomeScreen(apiClient: apiClient, session: session),
    );
  }
}
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.apiClient, required this.sessionStore, required this.onLoggedIn});
  final SapiSehatApiClient apiClient;
  final SessionStore sessionStore;
  final ValueChanged<AccountSession> onLoggedIn;
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final email = TextEditingController(text: 'farmer@example.com');
  final password = TextEditingController(text: 'strong-password');
  String? error;
  bool loading = false;

  Future<void> submit() async {
    setState(() => loading = true);
    try {
      final session = await widget.apiClient.loginFarmer(email.text, password.text);
      await widget.sessionStore.save(session);
      widget.onLoggedIn(session);
    } catch (_) {
      setState(() => error = 'Login gagal. Periksa email dan password.');
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(padding: const EdgeInsets.all(24), children: [
          const SizedBox(height: 40),
          const Text('SapiSehat', style: TextStyle(fontSize: 34, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          const Text('Risk signal, not diagnosis', style: TextStyle(fontSize: 16)),
          const SizedBox(height: 28),
          TextField(controller: email, decoration: const InputDecoration(labelText: 'Email'), keyboardType: TextInputType.emailAddress),
          const SizedBox(height: 12),
          TextField(controller: password, decoration: const InputDecoration(labelText: 'Password'), obscureText: true),
          const SizedBox(height: 20),
          FilledButton(onPressed: loading ? null : submit, child: Text(loading ? 'Memproses...' : 'Masuk')),
          if (error != null) Padding(padding: const EdgeInsets.only(top: 16), child: Text(error!, style: const TextStyle(color: Colors.red))),
        ]),
      ),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.apiClient, required this.session});
  final SapiSehatApiClient apiClient;
  final AccountSession session;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  var tab = 0;
  final localHistory = <ScanResult>[];

  @override
  Widget build(BuildContext context) {
    final pages = [
      CattleScreen(apiClient: widget.apiClient, session: widget.session),
      ScanScreen(apiClient: widget.apiClient, session: widget.session, onScan: (result) => setState(() => localHistory.insert(0, result))),
      HistoryScreen(apiClient: widget.apiClient, session: widget.session, localHistory: localHistory),
    ];
    return Scaffold(
      appBar: AppBar(
        title: const Text('SapiSehat'),
        actions: const [Padding(padding: EdgeInsets.only(right: 16), child: Center(child: Text('Risk signal, not diagnosis')))],
      ),
      body: pages[tab],
      bottomNavigationBar: NavigationBar(
        selectedIndex: tab,
        onDestinationSelected: (value) => setState(() => tab = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.pets), label: 'Sapi'),
          NavigationDestination(icon: Icon(Icons.camera_alt), label: 'Scan'),
          NavigationDestination(icon: Icon(Icons.history), label: 'Riwayat'),
        ],
      ),
    );
  }
}

class CattleScreen extends StatefulWidget {
  const CattleScreen({super.key, required this.apiClient, required this.session});
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  @override
  State<CattleScreen> createState() => _CattleScreenState();
}

class _CattleScreenState extends State<CattleScreen> {
  late Future<List<CattleProfile>> cattleFuture = widget.apiClient.listCattle(widget.session.farmerId);
  final tag = TextEditingController(text: 'SAPI-001');

  Future<void> addCattle() async {
    await widget.apiClient.createCattle(widget.session.farmerId, CattleDraft(tag: tag.text));
    setState(() => cattleFuture = widget.apiClient.listCattle(widget.session.farmerId));
  }

  @override
  Widget build(BuildContext context) {
    return ListView(padding: const EdgeInsets.all(20), children: [
      const _SectionHeader(title: 'Kandang Sapi', subtitle: 'Create, edit, and review cattle status before scan.'),
      const SizedBox(height: 16),
      _FieldCard(children: [
        TextField(controller: tag, decoration: const InputDecoration(labelText: 'Tag sapi')),
        const SizedBox(height: 12),
        FilledButton.icon(onPressed: addCattle, icon: const Icon(Icons.add), label: const Text('Tambah sapi')),
      ]),
      const SizedBox(height: 16),
      FutureBuilder<List<CattleProfile>>(
        future: cattleFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) return const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()));
          final cattle = snapshot.data ?? [];
          if (cattle.isEmpty) return const _EmptyState(icon: Icons.pets, title: 'Belum ada sapi', body: 'Tambah sapi pertama untuk mulai scan terhubung.');
          return Column(children: cattle.map((item) => _CattleCard(cattle: item)).toList());
        },
      ),
    ]);
  }
}

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key, required this.apiClient, required this.session, required this.onScan});
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final ValueChanged<ScanResult> onScan;
  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  ScanResult? result;
  bool loading = false;
  String? error;

  Future<void> runOnlineScan() async {
    setState(() { loading = true; error = null; });
    try {
      final scan = await widget.apiClient.uploadScan(farmerId: widget.session.farmerId, cattleId: 'cattle-1', bytes: [1, 2, 3]);
      widget.onScan(scan);
      setState(() => result = scan);
    } catch (_) {
      setState(() => error = 'Scan online gagal. Gunakan fallback offline lalu sinkronkan nanti.');
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> runOfflineFallback() async {
    final offline = ScanResult(localId: 'local-${DateTime.now().microsecondsSinceEpoch}', cattleId: 'cattle-1', label: 'needs_review', confidence: 0.0, capturedAt: DateTime.now(), inferenceMode: 'offline', syncStatus: 'pending_sync');
    widget.onScan(offline);
    setState(() => result = offline);
  }

  @override
  Widget build(BuildContext context) {
    return ListView(padding: const EdgeInsets.all(20), children: [
      const _SectionHeader(title: 'Scan Kamera', subtitle: 'Classify image with FastAPI, store scan image, or keep offline result for later sync.'),
      const SizedBox(height: 16),
      _HeroScanCard(onScan: loading ? null : runOnlineScan, onOffline: runOfflineFallback, loading: loading),
      if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: const TextStyle(color: Color(0xFF9A3412)))),
      if (result != null) Padding(padding: const EdgeInsets.only(top: 16), child: _ResultCard(result: result!)),
    ]);
  }
}

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key, required this.apiClient, required this.session, required this.localHistory});
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final List<ScanResult> localHistory;

  @override
  Widget build(BuildContext context) {
    return ListView(padding: const EdgeInsets.all(20), children: [
      const _SectionHeader(title: 'Riwayat Deteksi', subtitle: 'Review risk signals, sync state, and original capture time.'),
      const SizedBox(height: 16),
      FutureBuilder<List<DetectionHistoryItem>>(
        future: apiClient.listDetectionHistory(session.farmerId),
        builder: (context, snapshot) {
          final remote = snapshot.data ?? [];
          final cards = <Widget>[...localHistory.map((item) => _ResultCard(result: item)), ...remote.map((item) => _HistoryCard(item: item))];
          if (snapshot.connectionState != ConnectionState.done && cards.isEmpty) return const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()));
          if (cards.isEmpty) return const _EmptyState(icon: Icons.history, title: 'Belum ada riwayat', body: 'Hasil scan akan muncul di sini sebagai risk signal, bukan diagnosis.');
          return Column(children: cards);
        },
      ),
    ]);
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.subtitle});
  final String title;
  final String subtitle;
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        Text(subtitle, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: const Color(0xFF5B645B))),
      ]);
}

class _FieldCard extends StatelessWidget {
  const _FieldCard({required this.children});
  final List<Widget> children;
  @override
  Widget build(BuildContext context) => Card(elevation: 0, color: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: const BorderSide(color: Color(0xFFE0DED2))), child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: children)));
}

class _CattleCard extends StatelessWidget {
  const _CattleCard({required this.cattle});
  final CattleProfile cattle;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: const CircleAvatar(
            backgroundColor: Color(0xFFE6F2EA),
            child: Icon(Icons.pets, color: Color(0xFF2E6B4F)),
          ),
          title: Text(cattle.tag, style: const TextStyle(fontWeight: FontWeight.w700)),
          subtitle: const Text('Ready for cattle-first scan'),
          trailing: Chip(label: Text(cattle.status)),
        ),
      );
}

class _HeroScanCard extends StatelessWidget {
  const _HeroScanCard({required this.onScan, required this.onOffline, required this.loading});
  final VoidCallback? onScan;
  final VoidCallback onOffline;
  final bool loading;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(color: const Color(0xFF2E6B4F), borderRadius: BorderRadius.circular(28)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Icon(Icons.camera_alt, color: Colors.white, size: 42),
          const SizedBox(height: 16),
          const Text('Ambil gambar sapi', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          const Text('Online scan stores image governance metadata after prediction.', style: TextStyle(color: Color(0xFFEAF5EE))),
          const SizedBox(height: 18),
          FilledButton.tonal(onPressed: onScan, child: Text(loading ? 'Memproses...' : 'Scan online')),
          TextButton(onPressed: onOffline, child: const Text('Simpan offline fallback', style: TextStyle(color: Colors.white))),
        ]),
      );
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});
  final ScanResult result;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: Icon(result.inferenceMode == 'offline' ? Icons.cloud_off : Icons.verified_outlined),
          title: Text('Risk signal: ${result.label}'),
          subtitle: Text('${result.inferenceMode} • ${result.syncStatus} • ${result.capturedAt.toIso8601String()}'),
        ),
      );
}

class _HistoryCard extends StatelessWidget {
  const _HistoryCard({required this.item});
  final DetectionHistoryItem item;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: const Icon(Icons.assessment_outlined),
          title: Text(item.safeSummary),
          subtitle: Text('${item.inferenceMode} • ${(item.confidence * 100).round()}% confidence'),
        ),
      );
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.icon, required this.title, required this.body});
  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(children: [
            Icon(icon, size: 40),
            const SizedBox(height: 12),
            Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
            const SizedBox(height: 6),
            Text(body, textAlign: TextAlign.center),
          ]),
        ),
      );
}
