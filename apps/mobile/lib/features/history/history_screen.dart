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
    required this.onUpdateLocal,
    required this.onDeleteLocal,
  });
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final List<ScanResult> localHistory;
  final ValueChanged<ScanResult> onUpdateLocal;
  final ValueChanged<ScanResult> onDeleteLocal;

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  late Future<_HistoryData> historyFuture = loadHistory();
  final _remoteCattleOverrides = <String, String?>{};

  @override
  void didUpdateWidget(covariant HistoryScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    final oldLatest = oldWidget.localHistory.isEmpty
        ? null
        : oldWidget.localHistory.first.localId;
    final latest = widget.localHistory.isEmpty
        ? null
        : widget.localHistory.first.localId;
    if (oldLatest != latest) {
      historyFuture = loadHistory();
    }
  }

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

  Future<void> refresh() async {
    final future = loadHistory();
    setState(() {
      historyFuture = future;
    });
    await future;
  }

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: refresh,
    child: ListView(
      physics: const AlwaysScrollableScrollPhysics(),
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
            if (snapshot.connectionState != ConnectionState.done &&
                !snapshot.hasData) {
              return const Center(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: CircularProgressIndicator(),
                ),
              );
            }
            final data = snapshot.data ?? const _HistoryData();
            final cattleById = {for (final cow in data.cattle) cow.id: cow};
            final localById = {
              for (final item in widget.localHistory) item.localId: item,
            };
            final localItems = snapshot.hasError
                ? widget.localHistory
                : widget.localHistory.where(
                    (item) => item.syncStatus != 'synced',
                  );
            final cards = <Widget>[
              ...data.remote.map((item) {
                final effectiveCattleId =
                    _remoteCattleOverrides.containsKey(item.id)
                    ? _remoteCattleOverrides[item.id]
                    : item.cattleId;
                return _RemoteHistoryCard(
                  item: item,
                  effectiveCattleId: effectiveCattleId,
                  cattle: data.cattle,
                  cow: effectiveCattleId == null
                      ? null
                      : cattleById[effectiveCattleId],
                  apiClient: widget.apiClient,
                  session: widget.session,
                  imagePath: localById[item.id]?.imagePath,
                  onLinkedCowChanged: (cattleId) {
                    setState(() {
                      _remoteCattleOverrides[item.id] = cattleId;
                    });
                  },
                  onChanged: refresh,
                );
              }),
              ...localItems.map(
                (item) => _LocalResultCard(
                  result: item,
                  cattle: data.cattle,
                  cow: item.cattleId == null ? null : cattleById[item.cattleId],
                  apiClient: widget.apiClient,
                  session: widget.session,
                  onUpdate: widget.onUpdateLocal,
                  onChanged: refresh,
                  onDelete: () => widget.onDeleteLocal(item),
                ),
              ),
            ];
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
    ),
  );
}

class _LocalResultCard extends StatelessWidget {
  const _LocalResultCard({
    required this.result,
    required this.cattle,
    required this.apiClient,
    required this.session,
    required this.onUpdate,
    required this.onChanged,
    required this.onDelete,
    this.cow,
  });

  final ScanResult result;
  final List<CattleProfile> cattle;
  final CattleProfile? cow;
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final ValueChanged<ScanResult> onUpdate;
  final Future<void> Function() onChanged;
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
          onChangeCattle: (cattleId) async {
            onUpdate(
              result.copyWith(
                cattleId: cattleId,
                clearCattleId: cattleId == null,
              ),
            );
          },
          onChanged: onChanged,
          onDelete: () async => onDelete(),
        ),
      ),
    ),
    onEditCow: () async {
      final cattleId = await _openLinkedCowSelection(
        context,
        cattle,
        result.cattleId,
      );
      if (cattleId == _unchangedCattleSelection) return;
      onUpdate(
        result.copyWith(cattleId: cattleId, clearCattleId: cattleId == null),
      );
      await onChanged();
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sapi terkait berhasil diperbarui.')),
      );
    },
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
    required this.effectiveCattleId,
    required this.cattle,
    required this.apiClient,
    required this.session,
    required this.onLinkedCowChanged,
    required this.onChanged,
    this.imagePath,
    this.cow,
  });

  final DetectionHistoryItem item;
  final String? effectiveCattleId;
  final List<CattleProfile> cattle;
  final CattleProfile? cow;
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final String? imagePath;
  final ValueChanged<String?> onLinkedCowChanged;
  final Future<void> Function() onChanged;

  @override
  Widget build(BuildContext context) => _HistoryTile(
    title: cow == null ? item.label : _cowDisplayName(cow!),
    subtitle:
        item.createdAt?.toLocal().toString().split('.').first ??
        item.inferenceMode,
    label: item.label,
    confidence: item.confidence,
    imagePath: imagePath,
    onTap: () => Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ScanResultDetailPage(
          apiClient: apiClient,
          session: session,
          result: ScanResult(
            localId: item.id,
            cattleId: effectiveCattleId,
            label: item.label,
            confidence: item.confidence,
            capturedAt: item.createdAt ?? DateTime.now(),
            inferenceMode: item.inferenceMode,
            syncStatus: 'synced',
            imagePath: imagePath,
          ),
          image: imagePath == null ? null : XFile(imagePath!),
          cattle: cattle,
          skipAutoSave: true,
          onChangeCattle: (cattleId) async {
            await apiClient.updateDetectionHistoryCattle(
              farmerId: session.farmerId,
              resultId: item.id,
              cattleId: cattleId,
            );
            onLinkedCowChanged(cattleId);
          },
          onChanged: onChanged,
          onDelete: () async {
            await apiClient.deleteDetectionHistory(
              farmerId: session.farmerId,
              resultId: item.id,
            );
            await onChanged();
          },
        ),
      ),
    ),
    onEditCow: () async {
      final cattleId = await _openLinkedCowSelection(
        context,
        cattle,
        effectiveCattleId,
      );
      if (cattleId == _unchangedCattleSelection) return;
      try {
        await apiClient.updateDetectionHistoryCattle(
          farmerId: session.farmerId,
          resultId: item.id,
          cattleId: cattleId,
        );
        onLinkedCowChanged(cattleId);
      } catch (_) {
        if (!context.mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Gagal memperbarui sapi terkait.')),
        );
        return;
      }
      await _refreshAfterLinkChange(onChanged);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sapi terkait berhasil diperbarui.')),
      );
    },
    onDelete: () => _confirmDelete(
      context,
      title: 'Hapus riwayat ini?',
      message: 'Riwayat deteksi akan dihapus dari daftar.',
      onConfirm: () async {
        await apiClient.deleteDetectionHistory(
          farmerId: session.farmerId,
          resultId: item.id,
        );
        await onChanged();
      },
    ),
  );
}

Future<void> _refreshAfterLinkChange(Future<void> Function() refresh) async {
  try {
    await refresh();
  } catch (_) {
    // Best-effort refresh; link update already succeeded.
  }
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

const _unchangedCattleSelection = '__unchanged_cattle_selection__';

Future<String?> _openLinkedCowSelection(
  BuildContext context,
  List<CattleProfile> cattle,
  String? cattleId,
) async {
  final choice = await showDialog<_HistoryCowLinkChoice>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: const Text('Sapi terkait'),
      content: SizedBox(
        width: double.maxFinite,
        child: ListView(
          shrinkWrap: true,
          children: [
            ListTile(
              leading: Icon(
                cattleId == null
                    ? Icons.radio_button_checked
                    : Icons.radio_button_unchecked,
              ),
              title: const Text('Tidak dikaitkan'),
              onTap: () => Navigator.of(
                dialogContext,
              ).pop(const _HistoryCowLinkChoice(null)),
            ),
            for (final cow in cattle)
              ListTile(
                leading: Icon(
                  cow.id == cattleId
                      ? Icons.radio_button_checked
                      : Icons.radio_button_unchecked,
                ),
                title: Text(_cowDisplayName(cow)),
                subtitle: Text(cow.tag),
                onTap: () => Navigator.of(
                  dialogContext,
                ).pop(_HistoryCowLinkChoice(cow.id)),
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
  return choice == null ? _unchangedCattleSelection : choice.cattleId;
}

class _HistoryCowLinkChoice {
  const _HistoryCowLinkChoice(this.cattleId);
  final String? cattleId;
}

String _cowDisplayName(CattleProfile cow) {
  final name = cow.name?.trim();
  return name == null || name.isEmpty ? cow.tag : name;
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
  try {
    await onConfirm();
  } catch (_) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Gagal menghapus riwayat.')));
    return;
  }
  if (!context.mounted) return;
  ScaffoldMessenger.of(
    context,
  ).showSnackBar(const SnackBar(content: Text('Riwayat berhasil dihapus.')));
}

class _HistoryData {
  const _HistoryData({this.remote = const [], this.cattle = const []});
  final List<DetectionHistoryItem> remote;
  final List<CattleProfile> cattle;
}

enum _HistoryAction { editCow, delete }
