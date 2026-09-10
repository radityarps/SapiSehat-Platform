import 'dart:io';

import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../auth/auth.dart';
import 'guide_catalog.dart';

class GuideScreen extends StatefulWidget {
  const GuideScreen({
    super.key,
    required this.apiClient,
    required this.session,
    this.store,
  });
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final GuideCatalogStore? store;

  @override
  State<GuideScreen> createState() => _GuideScreenState();
}

class _GuideScreenState extends State<GuideScreen> {
  late final GuideCatalogStore store =
      widget.store ?? GuideCatalogStore(transport: widget.apiClient.transport);
  GuideCatalog? catalog;
  String query = '';
  String? categoryId;
  bool refreshFailed = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final active = await store.load();
    if (!mounted) return;
    setState(() => catalog = active);
    try {
      final refreshed = await store.refresh(widget.session, active);
      if (mounted) {
        setState(() {
          catalog = refreshed;
          refreshFailed = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => refreshFailed = true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final value = catalog;
    if (value == null) return const Center(child: CircularProgressIndicator());
    final locale = Localizations.localeOf(context).languageCode;
    final categories = [...value.categories]
      ..sort((a, b) => a.order.compareTo(b.order));
    final categoryById = {for (final item in categories) item.id: item};
    final q = query.trim().toLowerCase();
    final articles = value.articles.where((article) {
      final translation = article.translation(locale);
      final searchable = [
        translation.title,
        translation.summary,
        for (final block in translation.blocks)
          '${block.text ?? ''} ${(block.items ?? const []).join(' ')}',
      ].join(' ').toLowerCase();
      return (categoryId == null || article.categoryId == categoryId) &&
          (q.isEmpty || searchable.contains(q));
    }).toList()..sort((a, b) => b.publishedAt.compareTo(a.publishedAt));

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(
          'Panduan',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 8),
        const Text('Panduan penggunaan aplikasi, PMK, dan sapi sehat.'),
        if (refreshFailed) ...[
          const SizedBox(height: 10),
          MaterialBanner(
            content: const Text(
              'Pembaruan gagal. Panduan tersimpan tetap dapat digunakan.',
            ),
            actions: [
              TextButton(onPressed: _load, child: const Text('Coba lagi')),
            ],
          ),
        ],
        const SizedBox(height: 16),
        TextField(
          decoration: const InputDecoration(
            labelText: 'Cari panduan',
            prefixIcon: Icon(Icons.search),
            border: OutlineInputBorder(),
          ),
          onChanged: (value) => setState(() => query = value),
        ),
        const SizedBox(height: 14),
        SizedBox(
          height: 44,
          child: ListView(
            scrollDirection: Axis.horizontal,
            children: [
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: FilterChip(
                  selected: categoryId == null,
                  label: const Text('Semua'),
                  onSelected: (_) => setState(() => categoryId = null),
                ),
              ),
              for (final item in categories)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    selected: categoryId == item.id,
                    label: Text(item.label(locale)),
                    onSelected: (_) => setState(() => categoryId = item.id),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (articles.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text('Tidak ada panduan ditemukan'),
            ),
          )
        else
          for (final article in articles)
            GuideArticleCard(
              article: article,
              category: categoryById[article.categoryId]!,
              locale: locale,
              mediaPaths: value.mediaPaths,
            ),
      ],
    );
  }
}

class GuideDetailPage extends StatelessWidget {
  const GuideDetailPage({
    super.key,
    required this.article,
    required this.category,
    required this.locale,
    required this.mediaPaths,
  });
  final GuideArticle article;
  final GuideCategory category;
  final String locale;
  final Map<String, String> mediaPaths;

  @override
  Widget build(BuildContext context) {
    final translation = article.translation(locale);
    return Scaffold(
      appBar: AppBar(title: const Text('Panduan')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          GuideBadge(label: category.label(locale)),
          const SizedBox(height: 14),
          Text(
            translation.title,
            style: Theme.of(
              context,
            ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 10),
          Text(translation.summary),
          const SizedBox(height: 18),
          for (final block in translation.blocks) ...[
            _GuideBlockView(block: block, mediaPath: mediaPaths[block.mediaId]),
            const SizedBox(height: 14),
          ],
        ],
      ),
    );
  }
}

class _GuideBlockView extends StatelessWidget {
  const _GuideBlockView({required this.block, this.mediaPath});
  final GuideBlock block;
  final String? mediaPath;

  @override
  Widget build(BuildContext context) => switch (block.type) {
    'heading' => Text(
      block.text!,
      style: Theme.of(
        context,
      ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
    ),
    'paragraph' => Text(block.text!, style: const TextStyle(height: 1.45)),
    'bullet_list' => Column(
      children: [
        for (final item in block.items!)
          ListTile(dense: true, leading: const Text('•'), title: Text(item)),
      ],
    ),
    'image' when mediaPath != null => Semantics(
      image: true,
      label: block.alt,
      child: Image.file(File(mediaPath!), fit: BoxFit.cover),
    ),
    'image' => Text(block.alt ?? 'Gambar panduan tidak tersedia'),
    _ => const SizedBox.shrink(),
  };
}

class GuideArticleCard extends StatelessWidget {
  const GuideArticleCard({
    super.key,
    required this.article,
    required this.category,
    required this.locale,
    required this.mediaPaths,
  });
  final GuideArticle article;
  final GuideCategory category;
  final String locale;
  final Map<String, String> mediaPaths;

  @override
  Widget build(BuildContext context) {
    final translation = article.translation(locale);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => GuideDetailPage(
              article: article,
              category: category,
              locale: locale,
              mediaPaths: mediaPaths,
            ),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                translation.title,
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 6),
              Text(translation.summary),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Text(
                    'Baca →',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                  const Spacer(),
                  GuideBadge(label: category.label(locale)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class GuideBadge extends StatelessWidget {
  const GuideBadge({super.key, required this.label});
  final String label;

  @override
  Widget build(BuildContext context) => Align(
    alignment: Alignment.centerLeft,
    child: Chip(
      label: Text(label, style: const TextStyle(fontWeight: FontWeight.w800)),
    ),
  );
}
