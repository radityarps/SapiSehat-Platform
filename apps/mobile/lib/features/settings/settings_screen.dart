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
  final Future<void> Function() onLogout;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late AccountSession session;
  late Future<FarmerPreferences> future;

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

  Future<void> openDeleteAccount() async {
    final deleted = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => DeleteAccountPage(
          apiClient: widget.apiClient,
          session: session,
          sessionStore: widget.sessionStore,
        ),
      ),
    );
    if (deleted == true) widget.onArchived();
  }

  Future<void> confirmLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Keluar dari akun?'),
        content: const Text(
          'Anda perlu masuk lagi untuk menggunakan SapiSehat.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Keluar'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      await widget.onLogout();
      messenger.showSnackBar(const SnackBar(content: Text('Berhasil keluar.')));
    } catch (_) {
      messenger.showSnackBar(
        const SnackBar(content: Text('Gagal keluar. Coba lagi.')),
      );
    }
  }

  void openChangePassword() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) =>
            ChangePasswordPage(apiClient: widget.apiClient, session: session),
      ),
    );
  }

  void openTermsPrivacy() {
    Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => const TermsPrivacyPage()));
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
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: openEditProfile,
                    icon: const Icon(Icons.edit, size: 16),
                    label: const Text('Edit profil'),
                  ),
                  OutlinedButton.icon(
                    onPressed: openChangePassword,
                    icon: const Icon(Icons.lock_outline, size: 16),
                    label: const Text('Ubah password'),
                  ),
                ],
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
      Card(
        child: ListTile(
          leading: const Icon(Icons.description),
          title: const Text('Syarat & Privasi'),
          subtitle: const Text(
            'Baca ketentuan layanan dan kebijakan privasi SapiSehat.',
          ),
          trailing: const Icon(Icons.chevron_right),
          onTap: openTermsPrivacy,
        ),
      ),
      const SizedBox(height: 12),
      OutlinedButton(onPressed: confirmLogout, child: const Text('Keluar')),
      const SizedBox(height: 12),
      FilledButton.tonalIcon(
        onPressed: openDeleteAccount,
        icon: const Icon(Icons.delete_forever),
        label: const Text('Hapus akun'),
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

class DeleteAccountPage extends StatefulWidget {
  const DeleteAccountPage({
    super.key,
    required this.apiClient,
    required this.session,
    required this.sessionStore,
  });
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final SessionStore sessionStore;

  @override
  State<DeleteAccountPage> createState() => _DeleteAccountPageState();
}

class _DeleteAccountPageState extends State<DeleteAccountPage> {
  final password = TextEditingController();
  bool deleting = false;

  @override
  void dispose() {
    password.dispose();
    super.dispose();
  }

  Future<void> deleteAccount() async {
    if (password.text.length < 8) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Masukkan password akun.')));
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Hapus akun permanen?'),
        content: const Text(
          'Tindakan ini akan menghapus akses akun dan tidak dapat dibatalkan. Riwayat yang diwajibkan hukum dapat tetap disimpan sesuai kebijakan privasi.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Ya, hapus akun'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    setState(() => deleting = true);
    try {
      await widget.apiClient.deleteFarmerAccount(widget.session, password.text);
      await widget.sessionStore.clear();
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Gagal menghapus akun. Periksa password.'),
        ),
      );
    } finally {
      if (mounted) setState(() => deleting = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Hapus akun')),
    body: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Text(
              'Peringatan: penghapusan akun akan menonaktifkan akses Anda ke SapiSehat. Pastikan semua data penting sudah diekspor sebelum melanjutkan.',
            ),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: password,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Password',
            hintText: 'Masukkan password untuk konfirmasi',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: deleting ? null : deleteAccount,
          icon: const Icon(Icons.delete_forever),
          label: Text(deleting ? 'Menghapus...' : 'Hapus akun'),
        ),
      ],
    ),
  );
}

class ChangePasswordPage extends StatefulWidget {
  const ChangePasswordPage({
    super.key,
    required this.apiClient,
    required this.session,
  });
  final SapiSehatApiClient apiClient;
  final AccountSession session;

  @override
  State<ChangePasswordPage> createState() => _ChangePasswordPageState();
}

class _ChangePasswordPageState extends State<ChangePasswordPage> {
  final current = TextEditingController();
  final next = TextEditingController();
  final confirm = TextEditingController();
  bool saving = false;

  @override
  void dispose() {
    current.dispose();
    next.dispose();
    confirm.dispose();
    super.dispose();
  }

  Future<void> save() async {
    if (next.text.length < 8 || next.text != confirm.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Password baru minimal 8 karakter dan harus sama.'),
        ),
      );
      return;
    }
    setState(() => saving = true);
    try {
      await widget.apiClient.changePassword(
        widget.session,
        currentPassword: current.text,
        newPassword: next.text,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Password berhasil diubah.')),
      );
      Navigator.of(context).pop();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Gagal mengubah password.')));
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Ubah password')),
    body: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        TextField(
          controller: current,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Password saat ini',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: next,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Password baru',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: confirm,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Konfirmasi password baru',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: saving ? null : save,
          child: Text(saving ? 'Menyimpan...' : 'Simpan password'),
        ),
      ],
    ),
  );
}

class TermsPrivacyPage extends StatelessWidget {
  const TermsPrivacyPage({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Syarat & Privasi')),
    body: ListView(
      padding: const EdgeInsets.all(20),
      children: const [
        _LegalSection(
          title: 'Syarat Penggunaan',
          body:
              'SapiSehat menyediakan alat bantu deteksi dini berbasis foto dan data ternak. Hasil aplikasi adalah sinyal risiko, bukan diagnosis medis veteriner. Pengguna wajib menghubungi dokter hewan atau petugas kesehatan hewan untuk konfirmasi dan penanganan.',
        ),
        _LegalSection(
          title: 'Data yang Dikumpulkan',
          body:
              'Kami dapat memproses profil peternak, data sapi, foto scan, hasil prediksi, lokasi umum, preferensi notifikasi, serta riwayat aktivitas aplikasi untuk menyediakan layanan.',
        ),
        _LegalSection(
          title: 'Penggunaan Data',
          body:
              'Data digunakan untuk menjalankan deteksi, menyimpan riwayat, menyinkronkan perangkat, meningkatkan kualitas layanan, keamanan akun, dukungan pengguna, dan kepatuhan hukum.',
        ),
        _LegalSection(
          title: 'Berbagi Data',
          body:
              'Data tidak dijual. Data dapat dibagikan kepada penyedia infrastruktur, layanan analitik terbatas, atau otoritas/petugas terkait bila diwajibkan hukum atau diperlukan untuk kesehatan hewan.',
        ),
        _LegalSection(
          title: 'Keamanan & Retensi',
          body:
              'Kami menerapkan kontrol akses, autentikasi, dan perlindungan teknis yang wajar. Data disimpan selama akun aktif atau selama diperlukan untuk kewajiban operasional, hukum, audit, dan keamanan.',
        ),
        _LegalSection(
          title: 'Hak Pengguna',
          body:
              'Pengguna dapat memperbarui profil, meminta penghapusan akun, mengelola preferensi notifikasi, dan menghubungi pengelola layanan terkait akses atau koreksi data.',
        ),
        _LegalSection(
          title: 'Batasan Tanggung Jawab',
          body:
              'SapiSehat tidak menggantikan pemeriksaan dokter hewan. Keputusan perawatan, isolasi, vaksinasi, atau pengobatan harus mengikuti arahan profesional dan regulasi setempat.',
        ),
      ],
    ),
  );
}

class _LegalSection extends StatelessWidget {
  const _LegalSection({required this.title, required this.body});
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 18),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 6),
        Text(body, style: const TextStyle(height: 1.45)),
      ],
    ),
  );
}
