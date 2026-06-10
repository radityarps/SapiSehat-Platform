import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../features/auth/auth.dart';
import 'scan.dart';

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
    setState(() {
      loading = true;
      error = null;
    });
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
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const _ScanSectionHeader(title: 'Scan Kamera', subtitle: 'Classify image with FastAPI, store scan image, or keep offline result for later sync.'),
          const SizedBox(height: 16),
          _HeroScanCard(onScan: loading ? null : runOnlineScan, onOffline: runOfflineFallback, loading: loading),
          if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: const TextStyle(color: Color(0xFF9A3412)))),
          if (result != null) Padding(padding: const EdgeInsets.only(top: 16), child: _ResultCard(result: result!)),
        ],
      );
}

class _ScanSectionHeader extends StatelessWidget {
  const _ScanSectionHeader({required this.title, required this.subtitle});
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          Text(subtitle, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: const Color(0xFF5B645B))),
        ],
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
