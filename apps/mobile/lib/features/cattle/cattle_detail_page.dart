import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../auth/auth.dart';
import '../history/history.dart';
import 'cattle.dart';
import 'cattle_form_page.dart';

class CattleDetailPage extends StatefulWidget {
  const CattleDetailPage({
    super.key,
    required this.apiClient,
    required this.session,
    required this.cattle,
  });

  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final CattleProfile cattle;

  @override
  State<CattleDetailPage> createState() => _CattleDetailPageState();
}

class _CattleDetailPageState extends State<CattleDetailPage> {
  late CattleProfile cattle = widget.cattle;
  late Future<List<DetectionHistoryItem>> historyFuture = _loadHistory();

  String? get cattleName {
    final value = cattle.name?.trim();
    return value == null || value.isEmpty ? null : value;
  }

  Future<List<DetectionHistoryItem>> _loadHistory() async {
    final all = await widget.apiClient.listDetectionHistory(
      widget.session.farmerId,
    );
    return all.where((item) => item.cattleId == cattle.id).toList();
  }

  Future<void> edit() async {
    final result = await Navigator.of(context).push<CattleProfile>(
      MaterialPageRoute(
        builder: (_) => CattleFormPage(
          apiClient: widget.apiClient,
          session: widget.session,
          cattle: cattle,
        ),
      ),
    );
    if (result == null || !mounted) return;
    setState(() {
      cattle = result;
      historyFuture = _loadHistory();
    });
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Sapi berhasil diperbarui.')));
  }

  Future<void> delete() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Hapus sapi dari kandang?'),
        content: const Text(
          'Data akan diarsipkan, bukan dihapus permanen. Riwayat deteksi tetap tersimpan.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Arsipkan'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await widget.apiClient.archiveCattle(widget.session.farmerId, cattle.id);
      if (!mounted) return;
      Navigator.of(context).pop('archived');
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Gagal mengarsipkan sapi.')));
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Informasi Sapi')),
    body: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Card(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
            side: const BorderSide(color: Color(0xFFE0DED2)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const CircleAvatar(
                      backgroundColor: Color(0xFFE6F2EA),
                      child: Icon(Icons.pets, color: Color(0xFF2E6B4F)),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            cattleName ?? cattle.tag,
                            style: Theme.of(context).textTheme.titleLarge
                                ?.copyWith(fontWeight: FontWeight.w900),
                          ),
                          if (cattleName != null)
                            Text(
                              cattle.tag,
                              style: const TextStyle(color: Color(0xFF5B645B)),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                _Info(label: 'Status', value: cattle.status),
                _Info(label: 'Ras', value: cattle.breed),
                _Info(label: 'Jenis kelamin', value: cattle.sex),
                _Info(
                  label: 'Umur',
                  value: cattle.ageMonths == null
                      ? '-'
                      : '${cattle.ageMonths} bulan',
                ),
                _Info(label: 'Warna', value: cattle.color ?? '-'),
                _Info(
                  label: 'Bobot',
                  value: cattle.weightKg == null
                      ? '-'
                      : '${cattle.weightKg} kg',
                ),
                _Info(
                  label: 'Reproduksi',
                  value: cattle.isPregnant == true
                      ? 'Bunting'
                      : (cattle.reproductiveStatus ?? '-'),
                ),
                _Info(
                  label: 'Vaksin terakhir',
                  value: cattle.lastVaccinationDate ?? '-',
                ),
                _Info(
                  label: 'Obat cacing terakhir',
                  value: cattle.lastDewormingDate ?? '-',
                ),
                _Info(
                  label: 'Catatan kesehatan',
                  value: cattle.healthNotes ?? '-',
                ),
                _Info(label: 'Catatan', value: cattle.notes ?? '-'),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(
                      child: FilledButton.icon(
                        onPressed: edit,
                        icon: const Icon(Icons.edit),
                        label: const Text('Edit'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: delete,
                        icon: const Icon(Icons.delete_outline),
                        label: const Text('Hapus'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        Text(
          'Riwayat deteksi',
          style: Theme.of(
            context,
          ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 8),
        FutureBuilder<List<DetectionHistoryItem>>(
          future: historyFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: CircularProgressIndicator(),
                ),
              );
            }
            final items = snapshot.data ?? [];
            if (items.isEmpty) {
              return const Card(
                child: Padding(
                  padding: EdgeInsets.all(18),
                  child: Text('Belum ada riwayat deteksi untuk sapi ini.'),
                ),
              );
            }
            return Column(
              children: items
                  .map((item) => _DetectionCard(item: item))
                  .toList(),
            );
          },
        ),
      ],
    ),
  );
}

class _Info extends StatelessWidget {
  const _Info({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 130,
          child: Text(label, style: const TextStyle(color: Color(0xFF5B645B))),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
        ),
      ],
    ),
  );
}

class _DetectionCard extends StatelessWidget {
  const _DetectionCard({required this.item});
  final DetectionHistoryItem item;
  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      title: Text('Sinyal risiko: ${item.label}'),
      subtitle: Text(
        item.createdAt?.toLocal().toString().split('.').first ??
            item.inferenceMode,
      ),
      trailing: Text('${(item.confidence * 100).round()}%'),
    ),
  );
}
