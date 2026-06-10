import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../features/auth/auth.dart';
import 'cattle.dart';

class CattleScreen extends StatefulWidget {
  const CattleScreen({super.key, required this.apiClient, required this.session});
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  @override
  State<CattleScreen> createState() => _CattleScreenState();
}

class _CattleScreenState extends State<CattleScreen> {
  late Future<List<CattleProfile>> cattleFuture = widget.apiClient.listCattle(widget.session.farmerId);
  final tag = TextEditingController(text: 'SAPI-001');

  Future<void> addCattle() async {
    await widget.apiClient.createCattle(widget.session.farmerId, CattleDraft(tag: tag.text));
    setState(() => cattleFuture = widget.apiClient.listCattle(widget.session.farmerId));
  }

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(20), children: [
        const _SectionHeader(title: 'Kandang Sapi', subtitle: 'Create, edit, and review cattle status before scan.'),
        const SizedBox(height: 16),
        _FieldCard(children: [
          TextField(controller: tag, decoration: const InputDecoration(labelText: 'Tag sapi')),
          const SizedBox(height: 12),
          FilledButton.icon(onPressed: addCattle, icon: const Icon(Icons.add), label: const Text('Tambah sapi')),
        ]),
        const SizedBox(height: 16),
        FutureBuilder<List<CattleProfile>>(
          future: cattleFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) return const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()));
            final cattle = snapshot.data ?? [];
            if (cattle.isEmpty) return const _EmptyState(icon: Icons.pets, title: 'Belum ada sapi', body: 'Tambah sapi pertama untuk mulai scan terhubung.');
            return Column(children: cattle.map((item) => _CattleCard(cattle: item)).toList());
          },
        ),
      ]);
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.subtitle});
  final String title;
  final String subtitle;
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        Text(subtitle, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: const Color(0xFF5B645B))),
      ]);
}

class _FieldCard extends StatelessWidget {
  const _FieldCard({required this.children});
  final List<Widget> children;
  @override
  Widget build(BuildContext context) => Card(elevation: 0, color: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: const BorderSide(color: Color(0xFFE0DED2))), child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: children)));
}

class _CattleCard extends StatelessWidget {
  const _CattleCard({required this.cattle});
  final CattleProfile cattle;
  @override
  Widget build(BuildContext context) => Card(child: ListTile(leading: const CircleAvatar(backgroundColor: Color(0xFFE6F2EA), child: Icon(Icons.pets, color: Color(0xFF2E6B4F))), title: Text(cattle.tag, style: const TextStyle(fontWeight: FontWeight.w700)), subtitle: const Text('Ready for cattle-first scan'), trailing: Chip(label: Text(cattle.status))));
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.icon, required this.title, required this.body});
  final IconData icon;
  final String title;
  final String body;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(24), child: Column(children: [Icon(icon, size: 40), const SizedBox(height: 12), Text(title, style: const TextStyle(fontWeight: FontWeight.w800)), const SizedBox(height: 6), Text(body, textAlign: TextAlign.center)])));
}
