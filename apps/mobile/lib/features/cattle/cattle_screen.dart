import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../advisory/advisory.dart';
import '../auth/auth.dart';
import 'cattle.dart';
import 'cattle_detail_page.dart';
import 'cattle_form_page.dart';

class CattleScreen extends StatefulWidget {
  const CattleScreen({
    super.key,
    required this.apiClient,
    required this.session,
  });
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  @override
  State<CattleScreen> createState() => _CattleScreenState();
}

class _CattleScreenState extends State<CattleScreen> {
  var loading = true;
  String? error;
  List<CattleProfile> cattle = [];

  @override
  void initState() {
    super.initState();
    refresh(showLoading: true);
  }

  Future<void> refresh({bool showLoading = false}) async {
    if (showLoading && mounted) {
      setState(() {
        loading = true;
        error = null;
      });
    }
    try {
      final fresh = await widget.apiClient.listCattle(widget.session.farmerId);
      if (!mounted) return;
      setState(() {
        cattle = fresh;
        loading = false;
        error = null;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        loading = false;
        error = 'Gagal memuat daftar sapi.';
      });
    }
  }

  void toast(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> addCattle() async {
    final result = await Navigator.of(context).push<CattleProfile>(
      MaterialPageRoute(
        builder: (_) => CattleFormPage(
          apiClient: widget.apiClient,
          session: widget.session,
        ),
      ),
    );
    if (result != null) {
      await refresh(showLoading: true);
      if (!mounted) return;
      toast('Sapi berhasil ditambahkan.');
    }
  }

  Future<void> openDetail(CattleProfile item) async {
    final result = await Navigator.of(context).push<String>(
      MaterialPageRoute(
        builder: (_) => CattleDetailPage(
          apiClient: widget.apiClient,
          session: widget.session,
          cattle: item,
        ),
      ),
    );
    await refresh(showLoading: true);
    if (!mounted) return;
    if (result == 'archived') {
      toast('Sapi berhasil diarsipkan.');
    }
  }

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: refresh,
    child: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        AreaAdvisoryBanner(
          apiClient: widget.apiClient,
          session: widget.session,
        ),
        const SizedBox(height: 16),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: _SectionHeader(
                title: 'Kandang Sapi',
                subtitle:
                    'Kelola profil ternak, riwayat deteksi, dan status kandang.',
              ),
            ),
            FilledButton.icon(
              onPressed: addCattle,
              icon: const Icon(Icons.add),
              label: const Text('Tambah'),
            ),
          ],
        ),
        const SizedBox(height: 16),
        if (loading)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: CircularProgressIndicator(),
            ),
          )
        else if (error != null)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(error!),
            ),
          )
        else if (cattle.isEmpty)
          const _EmptyState(
            icon: Icons.pets,
            title: 'Belum ada sapi',
            body: 'Tambah sapi pertama untuk mulai scan terhubung.',
          )
        else
          Column(
            children: cattle
                .map(
                  (item) => _CattleCard(
                    key: ValueKey(item.id),
                    cattle: item,
                    onTap: () => openDetail(item),
                  ),
                )
                .toList(),
          ),
      ],
    ),
  );
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.subtitle});
  final String title;
  final String subtitle;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        title,
        style: Theme.of(
          context,
        ).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800),
      ),
      const SizedBox(height: 6),
      Text(
        subtitle,
        style: Theme.of(
          context,
        ).textTheme.bodyMedium?.copyWith(color: const Color(0xFF5B645B)),
      ),
    ],
  );
}

class _CattleCard extends StatelessWidget {
  const _CattleCard({super.key, required this.cattle, required this.onTap});
  final CattleProfile cattle;
  final VoidCallback onTap;

  String? get name {
    final value = cattle.name?.trim();
    return value == null || value.isEmpty ? null : value;
  }

  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      onTap: onTap,
      leading: const CircleAvatar(
        backgroundColor: Color(0xFFE6F2EA),
        child: Icon(Icons.pets, color: Color(0xFF2E6B4F)),
      ),
      title: Text(
        name ?? cattle.tag,
        style: const TextStyle(fontWeight: FontWeight.w700),
      ),
      subtitle: Text(
        [
          if (name != null) cattle.tag,
          'Status: ${cattle.status}',
          if (cattle.breed.isNotEmpty) 'Ras: ${cattle.breed}',
          if (cattle.weightKg != null) 'Bobot: ${cattle.weightKg} kg',
          if (cattle.isPregnant == true) 'Reproduksi: bunting',
        ].join('\n'),
      ),
      trailing: const Icon(Icons.chevron_right),
    ),
  );
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.icon,
    required this.title,
    required this.body,
  });
  final IconData icon;
  final String title;
  final String body;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Icon(icon, size: 40),
          const SizedBox(height: 12),
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          Text(body, textAlign: TextAlign.center),
        ],
      ),
    ),
  );
}
