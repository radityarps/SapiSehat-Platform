import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/api_client.dart';
import '../auth/auth.dart';
import '../cattle/cattle.dart';
import '../scan/scan.dart';
import '../scan/scan_result_detail_page.dart';
import 'history.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({
    super.key,
    required this.apiClient,
    required this.session,
    required this.localHistory,
    required this.onDeleteLocal,
  });
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final List<ScanResult> localHistory;
  final ValueChanged<ScanResult> onDeleteLocal;

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  late Future<_HistoryData> historyFuture = loadHistory();

  Future<_HistoryData> loadHistory() async {
    final results = await Future.wait([
      widget.apiClient.listDetectionHistory(widget.session.farmerId),
      widget.apiClient.listCattle(widget.session.farmerId),
    ]);
    return _HistoryData(
      remote: results[0] as List<DetectionHistoryItem>,
      cattle: results[1] as List<CattleProfile>,
    );
  }

  void refresh() => setState(() => historyFuture = loadHistory());

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(20),
    children: [
      Text(
        'Riwayat deteksi',
        style: Theme.of(
          context,
        ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
      ),
      const SizedBox(height: 8),
      const Text('Sinyal risiko tersimpan dengan waktu tangkap asli.'),
      const SizedBox(height: 16),
      FutureBuilder<_HistoryData>(
        future: historyFuture,
        builder: (context, snapshot) {
          final data = snapshot.data ?? const _HistoryData();
          final cattleById = {for (final cow in data.cattle) cow.id: cow};
          final cards = <Widget>[
            ...widget.localHistory.map(
              (item) => _LocalResultCard(
                result: item,
                cattle: data.cattle,
                cow: item.cattleId == null ? null : cattleById[item.cattleId],
                apiClient: widget.apiClient,
                session: widget.session,
                onChanged: refresh,
                onDelete: () => widget.onDeleteLocal(item),
              ),
            ),
            ...data.remote.map(
              (item) => _RemoteHistoryCard(
                item: item,
                cattle: data.cattle,
                cow: item.cattleId == null ? null : cattleById[item.cattleId],
                apiClient: widget.apiClient,
                session: widget.session,
                onChanged: refresh,
              ),
            ),
          ];
          if (snapshot.connectionState != ConnectionState.done &&
              cards.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: CircularProgressIndicator(),
              ),
            );
          }
          if (cards.isEmpty) {
            return const Card(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'Belum ada riwayat. Hasil scan muncul sebagai sinyal risiko, bukan diagnosis.',
                ),
              ),
            );
          }
          return Column(children: cards);
        },
      ),
    ],
  );
}

class _LocalResultCard extends StatelessWidget {
  const _LocalResultCard({
    required this.result,
    required this.cattle,
    required this.apiClient,
    required this.session,
    required this.onChanged,
    required this.onDelete,
    this.cow,
  });

  final ScanResult result;
  final List<CattleProfile> cattle;
  final CattleProfile? cow;
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final VoidCallback onChanged;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) => _HistoryTile(
    title: cow?.tag ?? result.label,
    subtitle: result.capturedAt.toLocal().toString().split('.').first,
    label: result.label,
    confidence: result.confidence,
    imagePath: result.imagePath,
    onTap: () => Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ScanResultDetailPage(
          apiClient: apiClient,
          session: session,
          result: result,
          image: result.imagePath == null ? null : XFile(result.imagePath!),
          cattle: cattle,
          skipAutoSave: true,
          onChanged: onChanged,
          onDelete: () async => onDelete(),
        ),
      ),
    ),
    onEditCow: () => _openLinkedCowSelection(context, cattle, result.cattleId),
    onDelete: () => _confirmDelete(
      context,
      title: 'Hapus riwayat ini?',
      message: 'Riwayat lokal akan dihapus dari daftar perangkat ini.',
      onConfirm: () async => onDelete(),
    ),
  );
}

class _RemoteHistoryCard extends StatelessWidget {
  const _RemoteHistoryCard({
    required this.item,
    required this.cattle,
    required this.apiClient,
    required this.session,
    required this.onChanged,
    this.cow,
  });

  final DetectionHistoryItem item;
  final List<CattleProfile> cattle;
  final CattleProfile? cow;
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) => _HistoryTile(
    title: cow?.tag ?? item.label,
    subtitle:
        item.createdAt?.toLocal().toString().split('.').first ??
        item.inferenceMode,
    label: item.label,
    confidence: item.confidence,
    onTap: () => Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ScanResultDetailPage(
          apiClient: apiClient,
          session: session,
          result: ScanResult(
            localId: item.id,
            cattleId: item.cattleId,
            label: item.label,
            confidence: item.confidence,
            capturedAt: item.createdAt ?? DateTime.now(),
            inferenceMode: item.inferenceMode,
            syncStatus: 'synced',
          ),
          image: null,
          cattle: cattle,
          skipAutoSave: true,
          onChanged: onChanged,
          onDelete: cow == null
              ? null
              : () async {
                  await apiClient.archiveCattle(session.farmerId, cow!.id);
                  onChanged();
                },
        ),
      ),
    ),
    onEditCow: () => _openLinkedCowSelection(context, cattle, item.cattleId),
    onDelete: cow == null
        ? null
        : () => _confirmDelete(
            context,
            title: 'Hapus sapi dari kandang?',
            message:
                'Data sapi akan diarsipkan, bukan dihapus permanen. Riwayat deteksi tetap tersimpan.',
            onConfirm: () async {
              await apiClient.archiveCattle(session.farmerId, cow!.id);
              onChanged();
            },
          ),
  );
}

class _HistoryTile extends StatelessWidget {
  const _HistoryTile({
    required this.title,
    required this.subtitle,
    required this.label,
    required this.confidence,
    required this.onTap,
    this.imagePath,
    this.onEditCow,
    this.onDelete,
  });

  final String title;
  final String subtitle;
  final String label;
  final double confidence;
  final String? imagePath;
  final VoidCallback onTap;
  final VoidCallback? onEditCow;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      onTap: onTap,
      leading: _HistoryPreview(imagePath: imagePath, label: label),
      title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text('$label • $subtitle'),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('${(confidence * 100).round()}%'),
          PopupMenuButton<_HistoryAction>(
            onSelected: (action) {
              switch (action) {
                case _HistoryAction.editCow:
                  onEditCow?.call();
                case _HistoryAction.delete:
                  onDelete?.call();
              }
            },
            itemBuilder: (context) => [
              if (onEditCow != null)
                const PopupMenuItem(
                  value: _HistoryAction.editCow,
                  child: Text('Edit sapi'),
                ),
              if (onDelete != null)
                const PopupMenuItem(
                  value: _HistoryAction.delete,
                  child: Text('Hapus'),
                ),
            ],
          ),
        ],
      ),
    ),
  );
}

class _HistoryPreview extends StatelessWidget {
  const _HistoryPreview({this.imagePath, required this.label});
  final String? imagePath;
  final String label;

  @override
  Widget build(BuildContext context) {
    final path = imagePath;
    final file = path == null ? null : File(path);
    final hasImage = file != null && file.existsSync();
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 56,
        height: 56,
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        child: hasImage
            ? Image.file(file, fit: BoxFit.cover)
            : Center(
                child: Text(
                  label.characters.take(3).toString().toUpperCase(),
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
      ),
    );
  }
}

Future<void> _openLinkedCowSelection(
  BuildContext context,
  List<CattleProfile> cattle,
  String? cattleId,
) async {
  await showDialog<CattleProfile>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: const Text('Sapi terkait'),
      content: SizedBox(
        width: double.maxFinite,
        child: ListView(
          shrinkWrap: true,
          children: [
            for (final cow in cattle)
              ListTile(
                leading: Icon(
                  cow.id == cattleId
                      ? Icons.radio_button_checked
                      : Icons.radio_button_unchecked,
                ),
                title: Text(cow.tag),
                subtitle: Text(cow.name ?? cow.breed),
                onTap: () => Navigator.of(dialogContext).pop(cow),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(dialogContext).pop(),
          child: const Text('Tutup'),
        ),
      ],
    ),
  );
}

Future<void> _confirmDelete(
  BuildContext context, {
  required String title,
  required String message,
  required Future<void> Function() onConfirm,
}) async {
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(dialogContext).pop(false),
          child: const Text('Batal'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(dialogContext).pop(true),
          child: const Text('Hapus'),
        ),
      ],
    ),
  );
  if (confirmed != true) return;
  await onConfirm();
}

class _HistoryData {
  const _HistoryData({this.remote = const [], this.cattle = const []});
  final List<DetectionHistoryItem> remote;
  final List<CattleProfile> cattle;
}

enum _HistoryAction { editCow, delete }
