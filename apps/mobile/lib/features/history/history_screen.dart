import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../auth/auth.dart';
import '../scan/scan.dart';
import 'history.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key, required this.apiClient, required this.session, required this.localHistory});
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final List<ScanResult> localHistory;

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(20), children: [
        Text('Riwayat deteksi', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        const Text('Sinyal risiko tersimpan dengan status sinkronisasi dan waktu tangkap asli.'),
        const SizedBox(height: 16),
        FutureBuilder<List<DetectionHistoryItem>>(
          future: apiClient.listDetectionHistory(session.farmerId),
          builder: (context, snapshot) {
            final remote = snapshot.data ?? [];
            final cards = <Widget>[...localHistory.map((item) => _ResultCard(result: item)), ...remote.map((item) => _HistoryCard(item: item))];
            if (snapshot.connectionState != ConnectionState.done && cards.isEmpty) return const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()));
            if (cards.isEmpty) return const Card(child: Padding(padding: EdgeInsets.all(24), child: Text('Belum ada riwayat. Hasil scan muncul sebagai sinyal risiko, bukan diagnosis.')));
            return Column(children: cards);
          },
        ),
      ]);
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});
  final ScanResult result;
  @override
  Widget build(BuildContext context) => Card(child: ListTile(title: Text('Sinyal risiko: ${result.label}'), subtitle: Text('${result.inferenceMode} • ${result.syncStatus}'), trailing: Text('${(result.confidence * 100).round()}%')));
}

class _HistoryCard extends StatelessWidget {
  const _HistoryCard({required this.item});
  final DetectionHistoryItem item;
  @override
  Widget build(BuildContext context) => Card(child: ListTile(title: Text(item.safeSummary.replaceFirst('Risk signal', 'Sinyal risiko')), subtitle: Text(item.inferenceMode), trailing: Text('${(item.confidence * 100).round()}%')));
}
