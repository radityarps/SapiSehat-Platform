import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../auth/auth.dart';
import '../profile/profile_screen.dart';
import 'settings.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({
    super.key,
    required this.apiClient,
    required this.session,
    required this.sessionStore,
    required this.onSessionChanged,
    required this.onArchived,
    required this.onLogout,
  });
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final SessionStore sessionStore;
  final ValueChanged<AccountSession> onSessionChanged;
  final VoidCallback onArchived;
  final VoidCallback onLogout;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late AccountSession session;
  late Future<FarmerPreferences> future;
  final password = TextEditingController();

  @override
  void initState() {
    super.initState();
    session = widget.session;
    future = widget.apiClient.getPreferences(session);
  }

  Future<void> save(FarmerPreferences prefs) async {
    final next = await widget.apiClient.updatePreferences(session, prefs);
    setState(() => future = Future.value(next));
  }

  Future<void> archive() async {
    await widget.apiClient.archiveFarmerAccount(session, password.text);
    await widget.sessionStore.clear();
    widget.onArchived();
  }

  void openEditProfile() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ProfileScreen(
          apiClient: widget.apiClient,
          session: session,
          onSessionChanged: (updated) {
            setState(() => session = updated);
            widget.onSessionChanged(updated);
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(20),
    children: [
      Text(
        'Pengaturan',
        style: Theme.of(
          context,
        ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
      ),
      const SizedBox(height: 16),

      // Profile card
      Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    radius: 24,
                    backgroundColor: const Color(0xFF2E6B4F),
                    child: Text(
                      session.name.isNotEmpty
                          ? session.name[0].toUpperCase()
                          : 'P',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          session.name.isEmpty ? 'Demo Farmer' : session.name,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          session.email,
                          style: const TextStyle(
                            color: Colors.grey,
                            fontSize: 13,
                          ),
                        ),
                        if (session.address != null &&
                            session.address!.isNotEmpty)
                          Text(
                            session.address!,
                            style: const TextStyle(
                              color: Colors.grey,
                              fontSize: 12,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        Text(
                          session.jurisdictionId,
                          style: const TextStyle(
                            color: Colors.grey,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: openEditProfile,
                icon: const Icon(Icons.edit, size: 16),
                label: const Text('Edit profil'),
              ),
            ],
          ),
        ),
      ),
      const SizedBox(height: 16),

      // Preferences card
      FutureBuilder<FarmerPreferences>(
        future: future,
        builder: (context, snapshot) {
          final prefs =
              snapshot.data ?? FarmerPreferences(farmerId: session.farmerId);
          return Card(
            child: Column(
              children: [
                SwitchListTile(
                  value: prefs.scanResultNotifications,
                  onChanged: (v) =>
                      save(prefs.copyWith(scanResultNotifications: v)),
                  title: const Text('Notifikasi hasil scan'),
                ),
                SwitchListTile(
                  value: prefs.syncNotifications,
                  onChanged: (v) => save(prefs.copyWith(syncNotifications: v)),
                  title: const Text('Notifikasi sinkronisasi'),
                ),
                SwitchListTile(
                  value: prefs.areaRiskAdvisoryNotifications,
                  onChanged: (v) =>
                      save(prefs.copyWith(areaRiskAdvisoryNotifications: v)),
                  title: const Text('Notifikasi sinyal risiko wilayah'),
                ),
                SwitchListTile(
                  value: prefs.followUpStatusNotifications,
                  onChanged: (v) =>
                      save(prefs.copyWith(followUpStatusNotifications: v)),
                  title: const Text('Notifikasi status tindak lanjut'),
                ),
                SwitchListTile(
                  value: prefs.quietHoursEnabled,
                  onChanged: (v) => save(prefs.copyWith(quietHoursEnabled: v)),
                  title: const Text('Jam tenang'),
                ),
              ],
            ),
          );
        },
      ),
      const SizedBox(height: 12),
      const _InfoCard(
        icon: Icons.camera_alt,
        title: 'Izin kamera',
        body:
            'Dipakai untuk mengambil foto deteksi. Buka pengaturan sistem bila izin ditolak.',
      ),
      const _InfoCard(
        icon: Icons.photo_library,
        title: 'Izin galeri',
        body: 'Dipakai saat memilih foto yang sudah ada untuk scan.',
      ),
      const _InfoCard(
        icon: Icons.location_on,
        title: 'Izin lokasi',
        body:
            'Dipakai untuk mengisi alamat dari GPS. Alamat tetap perlu dikonfirmasi.',
      ),
      const _InfoCard(
        icon: Icons.description,
        title: 'Terms & privacy checklist',
        body:
            'SapiSehat memberi sinyal risiko, bukan diagnosis. Foto scan disimpan untuk pemantauan dan tindak lanjut.',
      ),
      const SizedBox(height: 12),
      OutlinedButton(onPressed: widget.onLogout, child: const Text('Keluar')),
      const SizedBox(height: 12),
      TextField(
        controller: password,
        obscureText: true,
        decoration: const InputDecoration(
          labelText: 'Password untuk arsip akun',
        ),
      ),
      const SizedBox(height: 8),
      FilledButton.tonal(
        onPressed: archive,
        child: const Text('Arsipkan akun'),
      ),
    ],
  );
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({
    required this.icon,
    required this.title,
    required this.body,
  });
  final IconData icon;
  final String title;
  final String body;
  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      leading: Icon(icon),
      title: Text(title),
      subtitle: Text(body),
    ),
  );
}
