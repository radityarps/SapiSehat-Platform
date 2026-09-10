import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../auth/auth.dart';
import 'cattle.dart';

class CattleFormPage extends StatefulWidget {
  const CattleFormPage({
    super.key,
    required this.apiClient,
    required this.session,
    this.cattle,
  });

  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final CattleProfile? cattle;

  @override
  State<CattleFormPage> createState() => _CattleFormPageState();
}

class _CattleFormPageState extends State<CattleFormPage> {
  final formKey = GlobalKey<FormState>();
  late final tag = TextEditingController(text: widget.cattle?.tag ?? '');
  late final name = TextEditingController(text: widget.cattle?.name ?? '');
  late final breed = TextEditingController(
    text: widget.cattle?.breed ?? 'Sapi Bali',
  );
  late final color = TextEditingController(text: widget.cattle?.color ?? '');
  late final ageMonths = TextEditingController(
    text: widget.cattle?.ageMonths?.toString() ?? '24',
  );
  late final weight = TextEditingController(
    text: widget.cattle?.weightKg?.toString() ?? '',
  );
  late final lastCalvingDate = TextEditingController(
    text: widget.cattle?.lastCalvingDate ?? '',
  );
  late final vaccinationDate = TextEditingController(
    text: widget.cattle?.lastVaccinationDate ?? '',
  );
  late final dewormingDate = TextEditingController(
    text: widget.cattle?.lastDewormingDate ?? '',
  );
  late final healthNotes = TextEditingController(
    text: widget.cattle?.healthNotes ?? '',
  );
  late final purchaseDate = TextEditingController(
    text: widget.cattle?.purchaseDate ?? '',
  );
  late final purchasePrice = TextEditingController(
    text: widget.cattle?.purchasePriceIdr?.toString() ?? '',
  );
  late final notes = TextEditingController(text: widget.cattle?.notes ?? '');
  late String sex = widget.cattle?.sex ?? 'female';
  late String status = widget.cattle?.status ?? 'active';
  late bool isPregnant = widget.cattle?.isPregnant ?? false;
  bool saving = false;

  bool get editing => widget.cattle != null;

  @override
  void dispose() {
    for (final controller in [
      tag,
      name,
      breed,
      color,
      ageMonths,
      weight,
      lastCalvingDate,
      vaccinationDate,
      dewormingDate,
      healthNotes,
      purchaseDate,
      purchasePrice,
      notes,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> save() async {
    if (!formKey.currentState!.validate()) return;
    setState(() => saving = true);
    final draft = CattleDraft(
      tag: tag.text.trim(),
      sex: sex,
      breed: breed.text.trim(),
      ageMonths: int.parse(ageMonths.text.trim()),
      status: status,
      jurisdictionId: widget.session.jurisdictionId,
      name: _emptyToNull(name.text),
      color: _emptyToNull(color.text),
      weightKg: double.tryParse(weight.text.replaceAll(',', '.')),
      reproductiveStatus: isPregnant
          ? 'pregnant'
          : widget.cattle?.reproductiveStatus,
      isPregnant: isPregnant,
      lastCalvingDate: _emptyToNull(lastCalvingDate.text),
      lastVaccinationDate: _emptyToNull(vaccinationDate.text),
      lastDewormingDate: _emptyToNull(dewormingDate.text),
      healthNotes: _emptyToNull(healthNotes.text),
      purchaseDate: _emptyToNull(purchaseDate.text),
      purchasePriceIdr: int.tryParse(purchasePrice.text.trim()),
      notes: _emptyToNull(notes.text),
    );
    try {
      final result = editing
          ? await widget.apiClient.updateCattle(
              widget.session.farmerId,
              draft.toProfile(widget.cattle!),
            )
          : await widget.apiClient.createCattle(widget.session.farmerId, draft);
      if (!mounted) return;
      Navigator.of(context).pop(result);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            editing ? 'Gagal memperbarui sapi.' : 'Gagal menambahkan sapi.',
          ),
        ),
      );
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(editing ? 'Edit sapi' : 'Tambah sapi')),
    body: SafeArea(
      child: Form(
        key: formKey,
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Text(
              editing ? 'Edit data sapi' : 'Tambah data sapi',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Tanda * wajib diisi. Data ini membantu scan terhubung ke sapi yang tepat.',
            ),
            const SizedBox(height: 20),
            _text(tag, 'Tag sapi *', required: true, hint: 'Contoh: SAPI-001'),
            _gap(),
            _text(name, 'Nama sapi', hint: 'Opsional'),
            _gap(),
            DropdownButtonFormField<String>(
              initialValue: sex,
              decoration: const InputDecoration(
                labelText: 'Jenis kelamin *',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'female', child: Text('Betina')),
                DropdownMenuItem(value: 'male', child: Text('Jantan')),
                DropdownMenuItem(
                  value: 'unknown',
                  child: Text('Tidak diketahui'),
                ),
              ],
              onChanged: (value) => setState(() => sex = value ?? 'female'),
            ),
            _gap(),
            DropdownButtonFormField<String>(
              initialValue: status,
              decoration: const InputDecoration(
                labelText: 'Status *',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'active', child: Text('Aktif')),
                DropdownMenuItem(value: 'sold', child: Text('Terjual')),
                DropdownMenuItem(value: 'dead', child: Text('Mati')),
                DropdownMenuItem(value: 'lost', child: Text('Hilang')),
              ],
              onChanged: (value) => setState(() => status = value ?? 'active'),
            ),
            _gap(),
            _text(breed, 'Ras *', required: true, hint: 'Contoh: Sapi Bali'),
            _gap(),
            _text(
              ageMonths,
              'Umur (bulan) *',
              required: true,
              numeric: true,
              hint: 'Contoh: 24',
            ),
            _gap(),
            _text(color, 'Warna', hint: 'Contoh: coklat'),
            _gap(),
            _text(weight, 'Bobot (kg)', decimal: true, hint: 'Contoh: 280'),
            _gap(),
            Card(
              child: SwitchListTile(
                value: isPregnant,
                title: const Text('Sedang bunting'),
                subtitle: const Text('Khusus sapi betina bila diketahui'),
                onChanged: (value) => setState(() => isPregnant = value),
              ),
            ),
            _gap(),
            _dateField(
              lastCalvingDate,
              'Tanggal melahirkan terakhir',
            ),
            _gap(),
            _dateField(
              vaccinationDate,
              'Tanggal vaksin terakhir',
            ),
            _gap(),
            _dateField(
              dewormingDate,
              'Tanggal obat cacing terakhir',
            ),
            _gap(),
            _text(
              healthNotes,
              'Catatan kesehatan',
              maxLines: 2,
              hint: 'Catatan aman, bukan diagnosis',
            ),
            _gap(),
            _dateField(
              purchaseDate,
              'Tanggal pembelian',
            ),
            _gap(),
            _text(
              purchasePrice,
              'Harga pembelian (Rp)',
              numeric: true,
              hint: '15000000',
            ),
            _gap(),
            _text(notes, 'Catatan tambahan', maxLines: 2),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: saving ? null : save,
              child: Text(saving ? 'Menyimpan...' : 'Simpan'),
            ),
          ],
        ),
      ),
    ),
  );

  Widget _gap() => const SizedBox(height: 12);

  Widget _text(
    TextEditingController controller,
    String label, {
    bool required = false,
    bool numeric = false,
    bool decimal = false,
    int maxLines = 1,
    String? hint,
  }) => TextFormField(
    controller: controller,
    maxLines: maxLines,
    keyboardType: numeric || decimal
        ? TextInputType.numberWithOptions(decimal: decimal)
        : TextInputType.text,
    decoration: InputDecoration(
      labelText: label,
      hintText: hint,
      border: const OutlineInputBorder(),
    ),
    validator: (value) {
      final text = value?.trim() ?? '';
      if (required && text.isEmpty) {
        return '$label wajib diisi';
      }
      if (numeric && text.isNotEmpty && int.tryParse(text) == null) {
        return '$label harus angka bulat';
      }
      if (decimal &&
          text.isNotEmpty &&
          double.tryParse(text.replaceAll(',', '.')) == null) {
        return '$label harus angka';
      }
      return null;
    },
  );

  Widget _dateField(
    TextEditingController controller,
    String label, {
    String? hint = 'Pilih tanggal',
  }) => TextFormField(
    controller: controller,
    readOnly: true,
    onTap: () async {
      DateTime initial = DateTime.now();
      if (controller.text.trim().isNotEmpty) {
        final parsed = DateTime.tryParse(controller.text.trim());
        if (parsed != null) {
          if (parsed.isAfter(DateTime(2000)) &&
              parsed.isBefore(DateTime(2100))) {
            initial = parsed;
          }
        }
      }
      final picked = await showDatePicker(
        context: context,
        initialDate: initial,
        firstDate: DateTime(2000),
        lastDate: DateTime(2100),
      );
      if (picked != null) {
        final formatted =
            '${picked.year.toString().padLeft(4, '0')}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
        controller.text = formatted;
        setState(() {});
      }
    },
    decoration: InputDecoration(
      labelText: label,
      hintText: hint,
      border: const OutlineInputBorder(),
      prefixIcon: const Icon(Icons.calendar_today_outlined),
      suffixIcon: controller.text.isNotEmpty
          ? IconButton(
              icon: const Icon(Icons.clear),
              tooltip: 'Hapus tanggal',
              onPressed: () {
                controller.clear();
                setState(() {});
              },
            )
          : null,
    ),
  );
}

String? _emptyToNull(String value) {
  final text = value.trim();
  return text.isEmpty ? null : text;
}

extension on CattleDraft {
  CattleProfile toProfile(CattleProfile base) => base.copyWith(
    tag: tag,
    status: status,
    sex: sex,
    breed: breed,
    ageMonths: ageMonths,
    jurisdictionId: jurisdictionId,
    name: name,
    color: color,
    weightKg: weightKg,
    reproductiveStatus: reproductiveStatus,
    isPregnant: isPregnant,
    lastCalvingDate: lastCalvingDate,
    lastVaccinationDate: lastVaccinationDate,
    lastDewormingDate: lastDewormingDate,
    healthNotes: healthNotes,
    purchaseDate: purchaseDate,
    purchasePriceIdr: purchasePriceIdr,
    notes: notes,
  );
}
