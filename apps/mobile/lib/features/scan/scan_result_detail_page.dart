import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:pdf/widgets.dart' as pw;

import '../../core/api_client.dart';
import '../../features/auth/auth.dart';
import '../cattle/cattle.dart';
import 'scan.dart';

class ScanResultDetailPage extends StatefulWidget {
  const ScanResultDetailPage({
    super.key,
    required this.apiClient,
    required this.session,
    required this.result,
    required this.image,
    required this.cattle,
    this.skipAutoSave = false,
    this.onChanged,
    this.onDelete,
    this.onChangeCattle,
  });

  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final ScanDisplayResult result;
  final XFile? image;
  final List<CattleProfile> cattle;
  final bool skipAutoSave;
  final FutureOr<void> Function()? onChanged;
  final Future<void> Function()? onDelete;
  final Future<void> Function(String? cattleId)? onChangeCattle;

  @override
  State<ScanResultDetailPage> createState() => _ScanResultDetailPageState();
}

class _ScanResultDetailPageState extends State<ScanResultDetailPage> {
  late ScanDisplayResult result = widget.result;
  var saving = false;
  var saved = false;
  var allowPop = false;

  String? get _resultImagePath => widget.image?.path ?? result.imagePath;

  void closeWith(Object? value) {
    allowPop = true;
    Navigator.of(context).pop(value);
  }

  Future<ScanResult> save({String? cattleId}) async {
    final savedResult = await widget.apiClient.saveScanResult(
      farmerId: widget.session.farmerId,
      cattleId: cattleId,
      result: result as ScanResult,
    );
    result = savedResult;
    saved = true;
    return savedResult;
  }

  Future<void> saveWithDialog() async {
    final choice = await showDialog<_CowSaveChoice>(
      context: context,
      builder: (_) => _CowSelectDialog(cattle: widget.cattle),
    );
    if (choice == null || !choice.save) return;
    setState(() => saving = true);
    try {
      final savedResult = await save(cattleId: choice.cattleId);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Hasil scan disimpan.')));
      closeWith(savedResult);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Gagal menyimpan hasil scan.')),
      );
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Future<void> autoSaveAndClose() async {
    if (widget.skipAutoSave) {
      closeWith(null);
      return;
    }
    if (saving) return;
    if (saved) {
      closeWith(result);
      return;
    }
    setState(() => saving = true);
    try {
      final savedResult = await save();
      if (!mounted) return;
      closeWith(savedResult);
    } catch (_) {
      if (!mounted) return;
      final local = ScanResult(
        localId: result.localId,
        cattleId: result.cattleId,
        label: result.label,
        confidence: result.confidence,
        capturedAt: result.capturedAt,
        inferenceMode: result.inferenceMode,
        syncStatus: 'pending_sync',
        imagePath: widget.image?.path ?? result.imagePath,
        modelVersion: result.modelVersion,
        scores: result.scores,
      );
      closeWith(local);
    }
  }

  Future<void> editLinkedCow() async {
    final choice = await showDialog<_CowLinkChoice>(
      context: context,
      builder: (_) =>
          _LinkedCowDialog(cattle: widget.cattle, cattleId: result.cattleId),
    );
    if (choice == null || !mounted) return;
    try {
      await widget.onChangeCattle?.call(choice.cattleId);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Gagal memperbarui sapi terkait.')),
      );
      return;
    }
    if (!mounted) return;
    setState(() {
      result = result.copyWith(
        cattleId: choice.cattleId,
        clearCattleId: choice.cattleId == null,
      );
    });
    try {
      await widget.onChanged?.call();
    } catch (_) {
      // Best-effort refresh; link update already succeeded.
    }
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Sapi terkait berhasil diperbarui.')),
    );
  }

  Future<void> deleteResult() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Hapus riwayat ini?'),
        content: const Text(
          'Riwayat akan dihapus dari daftar. Tindakan ini membutuhkan konfirmasi.',
        ),
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
      await widget.onDelete?.call();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Gagal menghapus riwayat.')));
      return;
    }
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Riwayat berhasil dihapus.')));
    closeWith('deleted');
  }

  Future<void> sharePdf() async {
    try {
      final regularFont = await _loadPdfFont(
        '/system/fonts/Roboto-Regular.ttf',
      );
      final boldFont = await _loadPdfFont('/system/fonts/Roboto-Bold.ttf');
      final doc = pw.Document();
      doc.addPage(
        pw.Page(
          theme: pw.ThemeData.withFont(
            base: regularFont,
            bold: boldFont ?? regularFont,
          ),
          build: (context) => pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text(
                'SapiSehat - Laporan Sinyal Risiko',
                style: pw.TextStyle(
                  fontSize: 22,
                  fontWeight: pw.FontWeight.bold,
                ),
              ),
              pw.SizedBox(height: 16),
              pw.Text('Hasil ini adalah sinyal risiko, bukan diagnosis.'),
              pw.SizedBox(height: 12),
              pw.Text('Label: ${result.label}'),
              pw.Text('Keyakinan: ${(result.confidence * 100).round()}%'),
              pw.Text('Mode: ${result.inferenceMode}'),
              pw.Text('Waktu: ${result.capturedAt.toIso8601String()}'),
              pw.Text(
                'Sapi: ${_linkedCowLabel(widget.cattle, result.cattleId)}',
              ),
              pw.SizedBox(height: 12),
              pw.Text(
                'Tindakan pencegahan:',
                style: pw.TextStyle(fontWeight: pw.FontWeight.bold),
              ),
              for (final measure in _preventiveMeasures(result.label))
                pw.Bullet(text: measure),
            ],
          ),
        ),
      );
      final dir = await Directory.systemTemp.createTemp('sapisehat-scan');
      final file = File(
        '${dir.path}/sapisehat-scan-${DateTime.now().millisecondsSinceEpoch}.pdf',
      );
      await file.writeAsBytes(await doc.save());
      await const MethodChannel(
        'id.sapisehat/share',
      ).invokeMethod('shareFile', {
        'path': file.path,
        'mimeType': 'application/pdf',
        'text': 'Laporan sinyal risiko SapiSehat',
      });
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Gagal membuat PDF.')));
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: allowPop,
    onPopInvokedWithResult: (didPop, _) async {
      if (didPop) return;
      await autoSaveAndClose();
    },
    child: Scaffold(
      appBar: AppBar(title: const Text('Hasil deteksi')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Sinyal risiko: ${result.label}',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 14),
                  _ResultImagePreview(path: _resultImagePath),
                  const SizedBox(height: 12),
                  const Text(
                    'Hasil ini bukan diagnosis. Hubungi petugas bila ada gejala berlanjut.',
                  ),
                  const SizedBox(height: 16),
                  _Info(
                    label: 'Keyakinan',
                    value: '${(result.confidence * 100).round()}%',
                  ),
                  _Info(label: 'Mode', value: result.inferenceMode),
                  _Info(
                    label: 'Waktu',
                    value: result.capturedAt
                        .toLocal()
                        .toString()
                        .split('.')
                        .first,
                  ),
                  _Info(
                    label: 'Sapi',
                    value: _linkedCowLabel(widget.cattle, result.cattleId),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Tindakan pencegahan yang disarankan',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 10),
                  for (final measure in _preventiveMeasures(result.label))
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('• '),
                          Expanded(child: Text(measure)),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (!widget.skipAutoSave) ...[
            FilledButton.icon(
              onPressed: saving ? null : saveWithDialog,
              icon: const Icon(Icons.save),
              label: Text(saving ? 'Menyimpan...' : 'Simpan'),
            ),
            const SizedBox(height: 8),
          ],
          if (widget.skipAutoSave && widget.cattle.isNotEmpty) ...[
            OutlinedButton.icon(
              onPressed: editLinkedCow,
              icon: const Icon(Icons.edit_outlined),
              label: const Text('Edit sapi'),
            ),
            const SizedBox(height: 8),
          ],
          OutlinedButton.icon(
            onPressed: deleteResult,
            icon: const Icon(Icons.delete_outline),
            label: const Text('Hapus'),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: sharePdf,
            icon: const Icon(Icons.picture_as_pdf),
            label: const Text('Bagikan / Export PDF'),
          ),
          if (!widget.skipAutoSave) ...[
            const SizedBox(height: 8),
            TextButton.icon(
              onPressed: () => closeWith(null),
              icon: const Icon(Icons.refresh),
              label: const Text('Ulangi'),
            ),
          ],
        ],
      ),
    ),
  );
}

class _ResultImagePreview extends StatelessWidget {
  const _ResultImagePreview({this.path});
  final String? path;

  @override
  Widget build(BuildContext context) {
    final file = path == null ? null : File(path!);
    final hasImage = file != null && file.existsSync();
    return ClipRRect(
      borderRadius: BorderRadius.circular(18),
      child: Container(
        height: 180,
        width: double.infinity,
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        child: hasImage
            ? Image.file(file, fit: BoxFit.cover)
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.image_outlined,
                    size: 40,
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Preview gambar tidak tersedia',
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}

Future<pw.Font?> _loadPdfFont(String path) async {
  try {
    final bytes = await File(path).readAsBytes();
    return pw.Font.ttf(ByteData.sublistView(Uint8List.fromList(bytes)));
  } catch (_) {
    return null;
  }
}

List<String> _preventiveMeasures(String label) {
  final normalized = label.toLowerCase();
  if (normalized.contains('fmd') ||
      normalized.contains('pmk') ||
      normalized.contains('mulut') ||
      normalized.contains('kuku')) {
    return const [
      'Isolasi sapi bergejala dan hindari kontak dengan ternak sehat.',
      'Batasi lalu lintas orang, alat, pakan, dan kendaraan dari area kandang.',
      'Disinfeksi lantai, peralatan, sepatu, dan kendaraan secara rutin.',
      'Hubungi petugas kesehatan hewan untuk pemeriksaan dan arahan vaksinasi PMK.',
    ];
  }
  return const [
    'Pantau gejala selama beberapa hari dan catat perubahan kondisi sapi.',
    'Jaga kebersihan kandang, pakan, air minum, dan peralatan.',
    'Pisahkan sapi bila muncul demam, lesi kulit, air liur berlebih, atau pincang.',
    'Hubungi petugas kesehatan hewan bila gejala memburuk atau menyebar.',
  ];
}

class _LinkedCowDialog extends StatelessWidget {
  const _LinkedCowDialog({required this.cattle, this.cattleId});
  final List<CattleProfile> cattle;
  final String? cattleId;

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Pilih sapi terkait'),
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
            onTap: () => Navigator.of(context).pop(const _CowLinkChoice(null)),
          ),
          for (final cow in cattle)
            ListTile(
              leading: Icon(
                cow.id == cattleId
                    ? Icons.radio_button_checked
                    : Icons.radio_button_unchecked,
              ),
              title: Text(_formatCowName(cow)),
              subtitle: Text(cow.tag),
              onTap: () => Navigator.of(context).pop(_CowLinkChoice(cow.id)),
            ),
        ],
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.of(context).pop(),
        child: const Text('Batal'),
      ),
    ],
  );
}

class _CowLinkChoice {
  const _CowLinkChoice(this.cattleId);
  final String? cattleId;
}

String _formatCowName(CattleProfile cow) {
  final name = cow.name?.trim();
  return name == null || name.isEmpty ? cow.tag : name;
}

String _formatCowWithTag(CattleProfile cow) =>
    '${_formatCowName(cow)} (${cow.tag})';

String _linkedCowLabel(List<CattleProfile> cattle, String? cattleId) {
  if (cattleId == null) return 'Belum dikaitkan';
  for (final cow in cattle) {
    if (cow.id == cattleId) return _formatCowWithTag(cow);
  }
  return 'Belum dikaitkan';
}

class _CowSaveChoice {
  const _CowSaveChoice({required this.save, this.cattleId});
  final bool save;
  final String? cattleId;
}

class _CowSelectDialog extends StatefulWidget {
  const _CowSelectDialog({required this.cattle});
  final List<CattleProfile> cattle;
  @override
  State<_CowSelectDialog> createState() => _CowSelectDialogState();
}

class _CowSelectDialogState extends State<_CowSelectDialog> {
  CattleProfile? selected;

  String _cowLabel(CattleProfile cow) {
    final name = cow.name?.trim();
    final displayName = name == null || name.isEmpty ? cow.tag : name;
    return '$displayName (${cow.tag})';
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Simpan hasil scan'),
    actionsOverflowDirection: VerticalDirection.down,
    content: SingleChildScrollView(
      child: SizedBox(
        width: double.maxFinite,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Kaitkan ke sapi bila perlu. Pilihan ini opsional.'),
            const SizedBox(height: 12),
            DropdownButtonFormField<CattleProfile?>(
              initialValue: selected,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Sapi (opsional)',
                border: OutlineInputBorder(),
              ),
              items: [
                const DropdownMenuItem<CattleProfile?>(
                  value: null,
                  child: Text('Tidak dikaitkan'),
                ),
                ...widget.cattle.map(
                  (item) => DropdownMenuItem<CattleProfile?>(
                    value: item,
                    child: Text(
                      _cowLabel(item),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
              ],
              onChanged: (value) => setState(() => selected = value),
            ),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: () =>
            Navigator.of(context).pop(const _CowSaveChoice(save: true)),
        child: const Text('Simpan tanpa sapi'),
      ),
      FilledButton(
        onPressed: () => Navigator.of(
          context,
        ).pop(_CowSaveChoice(save: true, cattleId: selected?.id)),
        child: const Text('Simpan'),
      ),
    ],
  );
}

class _Info extends StatelessWidget {
  const _Info({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 96,
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
