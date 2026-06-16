import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;

import '../../core/api_client.dart';
import 'auth.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({
    super.key,
    required this.apiClient,
    required this.sessionStore,
    required this.onLoggedIn,
  });
  final SapiSehatApiClient apiClient;
  final SessionStore sessionStore;
  final ValueChanged<AccountSession> onLoggedIn;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final email = TextEditingController(
    text: kDebugMode ? 'farmer@example.com' : '',
  );
  final password = TextEditingController(
    text: kDebugMode ? 'strong-password' : '',
  );
  final name = TextEditingController(text: kDebugMode ? 'Demo Farmer' : '');
  final jurisdiction = TextEditingController(
    text: kDebugMode ? 'tembalang' : '',
  );
  final address = TextEditingController();

  bool registerMode = false;
  bool termsAccepted = false;
  bool showPassword = false;
  bool loading = false;
  bool gpsLoading = false;
  String? error;

  @override
  void dispose() {
    email.dispose();
    password.dispose();
    name.dispose();
    jurisdiction.dispose();
    address.dispose();
    super.dispose();
  }

  // Validation
  bool get emailValid =>
      RegExp(r'^[^@]+@[^@]+\.[^@]+').hasMatch(email.text.trim());
  bool get passwordValid => password.text.length >= 8;
  bool get nameValid => name.text.trim().length >= 2;
  bool get jurisdictionValid => jurisdiction.text.trim().isNotEmpty;

  bool get loginEnabled => emailValid && passwordValid && !loading;
  bool get registerEnabled =>
      emailValid &&
      passwordValid &&
      nameValid &&
      jurisdictionValid &&
      termsAccepted &&
      !loading;

  Future<void> fetchGpsAddress() async {
    setState(() {
      gpsLoading = true;
      error = null;
    });
    final ctx = context;
    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        setState(() => gpsLoading = false);
        if (!mounted) return;
        await showDialog(
          context: ctx,
          builder: (_) => AlertDialog(
            title: const Text('Layanan lokasi tidak aktif'),
            content: const Text(
              'Aktifkan GPS di pengaturan perangkat untuk mengisi alamat otomatis.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Batal'),
              ),
              FilledButton(
                onPressed: () {
                  Navigator.pop(ctx);
                  Geolocator.openLocationSettings();
                },
                child: const Text('Pengaturan'),
              ),
            ],
          ),
        );
        return;
      }

      LocationPermission perm = await Geolocator.checkPermission();

      if (perm == LocationPermission.deniedForever) {
        setState(() => gpsLoading = false);
        if (!mounted) return;
        await showDialog(
          context: ctx,
          builder: (_) => AlertDialog(
            title: const Text('Izin lokasi ditolak'),
            content: const Text(
              'Buka pengaturan aplikasi untuk mengizinkan akses lokasi.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Batal'),
              ),
              FilledButton(
                onPressed: () {
                  Navigator.pop(ctx);
                  Geolocator.openAppSettings();
                },
                child: const Text('Pengaturan'),
              ),
            ],
          ),
        );
        return;
      }

      if (perm == LocationPermission.denied) {
        setState(() => gpsLoading = false);
        if (!mounted) return;
        final confirmed = await showDialog<bool>(
          context: ctx,
          builder: (_) => AlertDialog(
            title: const Text('Izin lokasi diperlukan'),
            content: const Text(
              'SapiSehat membutuhkan izin lokasi untuk mengisi alamat otomatis dari GPS.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('Batal'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('Izinkan'),
              ),
            ],
          ),
        );
        if (confirmed != true) return;
        setState(() => gpsLoading = true);
        perm = await Geolocator.requestPermission();
        if (perm == LocationPermission.denied ||
            perm == LocationPermission.deniedForever) {
          setState(() {
            gpsLoading = false;
            error = 'Izin lokasi ditolak.';
          });
          return;
        }
      }

      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
        ),
      );
      final uri = Uri.parse(
        'https://nominatim.openstreetmap.org/reverse?lat=${pos.latitude}&lon=${pos.longitude}&format=json',
      );
      final resp = await http.get(
        uri,
        headers: {'User-Agent': 'SapiSehatApp/1.0'},
      );
      if (!mounted) return;
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        final addr = data['address'] as Map<String, dynamic>? ?? {};
        final district =
            (addr['subdistrict'] ??
                    addr['suburb'] ??
                    addr['city_district'] ??
                    addr['city'] ??
                    addr['town'] ??
                    '')
                as String;
        setState(() {
          address.text = data['display_name'] as String? ?? '';
          if (district.isNotEmpty) jurisdiction.text = district;
        });
      }
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => gpsLoading = false);
    }
  }

  Future<void> submit() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final session = registerMode
          ? await widget.apiClient.registerFarmer(
              FarmerRegistrationDraft(
                name: name.text.trim(),
                email: email.text.trim(),
                password: password.text,
                jurisdictionId: jurisdiction.text.trim(),
              ),
            )
          : await widget.apiClient.loginFarmer(
              email.text.trim(),
              password.text,
            );
      await widget.sessionStore.save(session);
      widget.onLoggedIn(session);
    } catch (_) {
      setState(
        () => error = registerMode
            ? 'Daftar gagal. Periksa data akun.'
            : 'Login gagal. Periksa email dan password.',
      );
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            const SizedBox(height: 24),
            Text(
              'SapiSehat',
              style: Theme.of(
                context,
              ).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 8),
            const Text(
              'Sinyal risiko, bukan diagnosis',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: false, label: Text('Masuk')),
                ButtonSegment(value: true, label: Text('Daftar')),
              ],
              selected: {registerMode},
              onSelectionChanged: (v) => setState(() {
                registerMode = v.first;
                error = null;
              }),
            ),
            const SizedBox(height: 18),

            // Register-only fields
            if (registerMode) ...[
              TextField(
                controller: name,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  labelText: 'Nama lengkap',
                  hintText: 'Masukkan nama Anda',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: TextField(
                      controller: jurisdiction,
                      onChanged: (_) => setState(() {}),
                      decoration: const InputDecoration(
                        labelText: 'Kecamatan/distrik',
                        hintText: 'Masukkan kecamatan Anda',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: TextField(
                      controller: address,
                      maxLines: 2,
                      decoration: const InputDecoration(
                        labelText: 'Alamat',
                        hintText: 'Masukkan alamat atau gunakan GPS',
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
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.my_location),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
            ],

            // Email
            TextField(
              controller: email,
              onChanged: (_) => setState(() {}),
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(
                labelText: 'Email',
                hintText: 'contoh@email.com',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),

            // Password
            TextField(
              controller: password,
              onChanged: (_) => setState(() {}),
              obscureText: !showPassword,
              decoration: InputDecoration(
                labelText: 'Password',
                hintText: 'Minimal 8 karakter',
                border: const OutlineInputBorder(),
                suffixIcon: IconButton(
                  icon: Icon(
                    showPassword ? Icons.visibility_off : Icons.visibility,
                  ),
                  onPressed: () => setState(() => showPassword = !showPassword),
                ),
              ),
            ),

            // Terms checkbox (register only)
            if (registerMode) ...[
              const SizedBox(height: 12),
              Card(
                child: CheckboxListTile(
                  value: termsAccepted,
                  onChanged: (v) => setState(() => termsAccepted = v ?? false),
                  title: const Text('Terms & privacy checklist'),
                  subtitle: const Text(
                    'Saya paham SapiSehat memberi sinyal risiko, bukan diagnosis. '
                    'Foto scan disimpan untuk pemantauan dan tindak lanjut.',
                  ),
                ),
              ),
            ],

            const SizedBox(height: 20),
            FilledButton(
              onPressed: (registerMode ? registerEnabled : loginEnabled)
                  ? submit
                  : null,
              child: Text(
                loading
                    ? 'Memproses...'
                    : (registerMode ? 'Daftar akun' : 'Masuk'),
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: null,
              child: const Text('Google login belum tersedia di perangkat ini'),
            ),
            if (error != null)
              Padding(
                padding: const EdgeInsets.only(top: 16),
                child: Text(
                  error!,
                  style: const TextStyle(color: Color(0xFFB42318)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
