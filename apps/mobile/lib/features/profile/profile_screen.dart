import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../auth/auth.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key, required this.apiClient, required this.session, required this.onSessionChanged});
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final ValueChanged<AccountSession> onSessionChanged;

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late final name = TextEditingController(text: widget.session.name.isEmpty ? 'Demo Farmer' : widget.session.name);
  late final jurisdiction = TextEditingController(text: widget.session.jurisdictionId);
  bool saving = false;

  Future<void> save() async {
    setState(() => saving = true);
    final updated = await widget.apiClient.updateFarmerProfile(widget.session, FarmerProfileDraft(name: name.text, jurisdictionId: jurisdiction.text));
    widget.onSessionChanged(updated);
    if (mounted) setState(() => saving = false);
  }

  void suggestGps() => setState(() => jurisdiction.text = 'tembalang');

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(20), children: [
        Text('Profil peternak', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        const Text('Wilayah dapat disarankan dari GPS, lalu tetap perlu dikonfirmasi manual.'),
        const SizedBox(height: 16),
        TextField(controller: name, decoration: const InputDecoration(labelText: 'Nama')),
        const SizedBox(height: 12),
        TextField(enabled: false, controller: TextEditingController(text: widget.session.email), decoration: const InputDecoration(labelText: 'Email')),
        const SizedBox(height: 12),
        TextField(controller: jurisdiction, decoration: const InputDecoration(labelText: 'Kecamatan/distrik')),
        const SizedBox(height: 8),
        OutlinedButton.icon(onPressed: suggestGps, icon: const Icon(Icons.my_location), label: const Text('Sarankan dari GPS')),
        const SizedBox(height: 8),
        const Text('Perubahan wilayah memengaruhi petugas kesehatan hewan lokal yang meninjau pengajuan berikutnya.'),
        const SizedBox(height: 16),
        FilledButton(onPressed: saving ? null : save, child: Text(saving ? 'Menyimpan...' : 'Simpan profil')),
      ]);
}
