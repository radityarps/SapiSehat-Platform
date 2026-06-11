import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import 'auth.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.apiClient, required this.sessionStore, required this.onLoggedIn});
  final SapiSehatApiClient apiClient;
  final SessionStore sessionStore;
  final ValueChanged<AccountSession> onLoggedIn;
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final email = TextEditingController(text: 'farmer@example.com');
  final password = TextEditingController(text: 'strong-password');
  final name = TextEditingController(text: 'Demo Farmer');
  final jurisdiction = TextEditingController(text: 'tembalang');
  bool registerMode = false;
  bool termsAccepted = false;
  String? error;
  bool loading = false;

  Future<void> submit() async {
    if (registerMode && !termsAccepted) {
      setState(() => error = 'Baca dan centang terms & privacy checklist sebelum daftar.');
      return;
    }
    setState(() { loading = true; error = null; });
    try {
      final session = registerMode
          ? await widget.apiClient.registerFarmer(FarmerRegistrationDraft(name: name.text, email: email.text, password: password.text, jurisdictionId: jurisdiction.text))
          : await widget.apiClient.loginFarmer(email.text, password.text);
      await widget.sessionStore.save(session);
      widget.onLoggedIn(session);
    } catch (_) {
      setState(() => error = registerMode ? 'Daftar gagal. Periksa data akun.' : 'Login gagal. Periksa email dan password.');
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: ListView(padding: const EdgeInsets.all(24), children: [
            const SizedBox(height: 24),
            Text('SapiSehat', style: Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            const Text('Sinyal risiko, bukan diagnosis', style: TextStyle(fontSize: 16)),
            const SizedBox(height: 20),
            SegmentedButton<bool>(
              segments: const [ButtonSegment(value: false, label: Text('Masuk')), ButtonSegment(value: true, label: Text('Daftar'))],
              selected: {registerMode},
              onSelectionChanged: (value) => setState(() => registerMode = value.first),
            ),
            const SizedBox(height: 18),
            if (registerMode) ...[
              TextField(controller: name, decoration: const InputDecoration(labelText: 'Nama')),
              const SizedBox(height: 12),
              TextField(controller: jurisdiction, decoration: const InputDecoration(labelText: 'Kecamatan/distrik')),
              const SizedBox(height: 8),
              OutlinedButton.icon(onPressed: () => setState(() => jurisdiction.text = 'tembalang'), icon: const Icon(Icons.my_location), label: const Text('Sarankan dari GPS')),
              const SizedBox(height: 12),
            ],
            TextField(controller: email, decoration: const InputDecoration(labelText: 'Email'), keyboardType: TextInputType.emailAddress),
            const SizedBox(height: 12),
            TextField(controller: password, decoration: const InputDecoration(labelText: 'Password'), obscureText: true),
            if (registerMode) ...[
              const SizedBox(height: 12),
              Card(
                child: CheckboxListTile(
                  value: termsAccepted,
                  onChanged: (value) => setState(() => termsAccepted = value ?? false),
                  title: const Text('Terms & privacy checklist'),
                  subtitle: const Text('Saya paham SapiSehat memberi sinyal risiko, bukan diagnosis. Foto scan disimpan untuk pemantauan dan tindak lanjut.'),
                ),
              ),
            ],
            const SizedBox(height: 20),
            FilledButton(onPressed: loading ? null : submit, child: Text(loading ? 'Memproses...' : (registerMode ? 'Daftar akun' : 'Masuk'))),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: null, child: const Text('Google login belum tersedia di perangkat ini')),
            if (error != null) Padding(padding: const EdgeInsets.only(top: 16), child: Text(error!, style: const TextStyle(color: Color(0xFFB42318)))),
          ]),
        ),
      );
}
