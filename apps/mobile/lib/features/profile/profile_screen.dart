import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;

import '../../core/api_client.dart';
import '../auth/auth.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({
    super.key,
    required this.apiClient,
    required this.session,
    required this.onSessionChanged,
  });
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final ValueChanged<AccountSession> onSessionChanged;

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late final name = TextEditingController(
    text: widget.session.name.isEmpty ? 'Demo Farmer' : widget.session.name,
  );
  late final jurisdiction = TextEditingController(text: widget.session.jurisdictionId);
  late final addressCtrl = TextEditingController(text: widget.session.address ?? '');
  bool saving = false;
  bool gpsLoading = false;
  String? error;

  @override
  void dispose() {
    name.dispose();
    jurisdiction.dispose();
    addressCtrl.dispose();
    super.dispose();
  }

  Future<void> fetchGpsAddress() async {
    setState(() { gpsLoading = true; error = null; });
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) throw Exception('Layanan lokasi tidak aktif.');
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) throw Exception('Izin lokasi ditolak.');
      }
      if (permission == LocationPermission.deniedForever) throw Exception('Izin lokasi ditolak permanen. Buka pengaturan perangkat.');
      final pos = await Geolocator.getCurrentPosition(locationSettings: const LocationSettings(accuracy: LocationAccuracy.medium));
      final uri = Uri.parse('https://nominatim.openstreetmap.org/reverse?lat=${pos.latitude}&lon=${pos.longitude}&format=json');
      final resp = await http.get(uri, headers: {'User-Agent': 'SapiSehatApp/1.0'});
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        final displayName = data['display_name'] as String? ?? '';
        setState(() => addressCtrl.text = displayName);
      }
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => gpsLoading = false);
    }
  }

  Future<void> save() async {
    setState(() { saving = true; error = null; });
    try {
      final updated = await widget.apiClient.updateFarmerProfile(
        widget.session,
        FarmerProfileDraft(
          name: name.text,
          jurisdictionId: jurisdiction.text,
          address: addressCtrl.text.isEmpty ? null : addressCtrl.text,
        ),
      );
      widget.onSessionChanged(updated);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profil berhasil disimpan.')),
        );
        Navigator.of(context).pop();
      }
    } catch (e) {
      setState(() => error = 'Gagal menyimpan profil.');
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Edit profil')),
        body: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            TextField(
              controller: name,
              decoration: const InputDecoration(labelText: 'Nama', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            TextField(
              enabled: false,
              controller: TextEditingController(text: widget.session.email),
              decoration: const InputDecoration(labelText: 'Email', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: jurisdiction,
              decoration: const InputDecoration(labelText: 'Kecamatan/distrik', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: TextField(
                    controller: addressCtrl,
                    maxLines: 2,
                    decoration: const InputDecoration(
                      labelText: 'Alamat',
                      hintText: 'Kosongkan atau isi manual / gunakan GPS',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                SizedBox(
                  height: 56,
                  child: OutlinedButton(
                    onPressed: gpsLoading ? null : fetchGpsAddress,
                    child: gpsLoading
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.my_location),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            const Text(
              'Tekan ikon lokasi untuk mengisi alamat otomatis dari GPS. Anda bisa mengedit hasilnya.',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
            if (error != null) ...[
              const SizedBox(height: 8),
              Text(error!, style: const TextStyle(color: Colors.red, fontSize: 13)),
            ],
            const SizedBox(height: 20),
            FilledButton(
              onPressed: saving ? null : save,
              child: Text(saving ? 'Menyimpan...' : 'Simpan profil'),
            ),
          ],
        ),
      );
}
