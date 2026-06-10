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
  String? error;
  bool loading = false;

  Future<void> submit() async {
    setState(() => loading = true);
    try {
      final session = await widget.apiClient.loginFarmer(email.text, password.text);
      await widget.sessionStore.save(session);
      widget.onLoggedIn(session);
    } catch (_) {
      setState(() => error = 'Login gagal. Periksa email dan password.');
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: ListView(padding: const EdgeInsets.all(24), children: [
            const SizedBox(height: 40),
            const Text('SapiSehat', style: TextStyle(fontSize: 34, fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            const Text('Risk signal, not diagnosis', style: TextStyle(fontSize: 16)),
            const SizedBox(height: 28),
            TextField(controller: email, decoration: const InputDecoration(labelText: 'Email'), keyboardType: TextInputType.emailAddress),
            const SizedBox(height: 12),
            TextField(controller: password, decoration: const InputDecoration(labelText: 'Password'), obscureText: true),
            const SizedBox(height: 20),
            FilledButton(onPressed: loading ? null : submit, child: Text(loading ? 'Memproses...' : 'Masuk')),
            if (error != null) Padding(padding: const EdgeInsets.only(top: 16), child: Text(error!, style: const TextStyle(color: Colors.red))),
          ]),
        ),
      );
}
