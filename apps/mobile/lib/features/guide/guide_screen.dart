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
  final TextEditingController _searchController = TextEditingController();
  GuideCatalog? catalog;
  String query = '';
  String? categoryId;
  bool refreshFailed = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
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
    if (value == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final theme = Theme.of(context);
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

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          children: [
            // Hero Header Card
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    theme.colorScheme.primaryContainer.withAlpha(220),
                    theme.colorScheme.primaryContainer.withAlpha(90),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: theme.colorScheme.primary.withAlpha(40),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              Icons.menu_book_rounded,
                              size: 20,
                              color: theme.colorScheme.primary,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Pusat Panduan',
                              style: theme.textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w900,
                                color: theme.colorScheme.onPrimaryContainer,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Edukasi kesehatan ternak, pencegahan penyakit PMK, dan tata cara aplikasi.',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.onPrimaryContainer.withAlpha(200),
                            height: 1.35,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.surface,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withAlpha(15),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Icon(
                      Icons.auto_stories_rounded,
                      size: 26,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                ],
              ),
            ),

            if (refreshFailed) ...[
              const SizedBox(height: 12),
              MaterialBanner(
                backgroundColor: theme.colorScheme.errorContainer.withAlpha(120),
                content: Text(
                  'Pembaruan katalog daring gagal. Panduan tersimpan tetap dapat dibaca secara offline.',
                  style: TextStyle(color: theme.colorScheme.onErrorContainer),
                ),
                actions: [
                  TextButton(
                    onPressed: _load,
                    child: const Text('Coba lagi'),
                  ),
                ],
              ),
            ],

            const SizedBox(height: 16),

            // Modern Search Bar
            TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Cari panduan, topik, atau kata kunci...',
                hintStyle: TextStyle(
                  fontSize: 14,
                  color: theme.colorScheme.onSurfaceVariant.withAlpha(160),
                ),
                prefixIcon: Icon(
                  Icons.search_rounded,
                  color: theme.colorScheme.primary,
                ),
                suffixIcon: query.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.close_rounded),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => query = '');
                        },
                      )
                    : null,
                filled: true,
                fillColor: theme.colorScheme.surface,
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(
                    color: theme.colorScheme.outlineVariant.withAlpha(130),
                  ),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(
                    color: theme.colorScheme.outlineVariant.withAlpha(130),
                  ),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(
                    color: theme.colorScheme.primary,
                    width: 1.5,
                  ),
                ),
              ),
              onChanged: (value) => setState(() => query = value),
            ),

            const SizedBox(height: 14),

            // Category Chips List
            SizedBox(
              height: 40,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: [
                  FilterChip(
                    selected: categoryId == null,
                    showCheckmark: false,
                    avatar: Icon(
                      Icons.grid_view_rounded,
                      size: 16,
                      color: categoryId == null
                          ? theme.colorScheme.onPrimary
                          : theme.colorScheme.onSurfaceVariant,
                    ),
                    label: Text('Semua (${value.articles.length})'),
                    labelStyle: TextStyle(
                      fontSize: 13,
                      fontWeight: categoryId == null
                          ? FontWeight.bold
                          : FontWeight.normal,
                      color: categoryId == null
                          ? theme.colorScheme.onPrimary
                          : theme.colorScheme.onSurface,
                    ),
                    selectedColor: theme.colorScheme.primary,
                    backgroundColor: theme.colorScheme.surface,
                    side: BorderSide(
                      color: categoryId == null
                          ? Colors.transparent
                          : theme.colorScheme.outlineVariant.withAlpha(140),
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(20),
                    ),
                    onSelected: (_) => setState(() => categoryId = null),
                  ),
                  const SizedBox(width: 8),
                  for (final item in categories) ...[
                    FilterChip(
                      selected: categoryId == item.id,
                      showCheckmark: false,
                      avatar: Icon(
                        _getCategoryIcon(item.id),
                        size: 16,
                        color: categoryId == item.id
                            ? theme.colorScheme.onPrimary
                            : theme.colorScheme.onSurfaceVariant,
                      ),
                      label: Text(
                        '${item.label(locale)} (${value.articles.where((a) => a.categoryId == item.id).length})',
                      ),
                      labelStyle: TextStyle(
                        fontSize: 13,
                        fontWeight: categoryId == item.id
                            ? FontWeight.bold
                            : FontWeight.normal,
                        color: categoryId == item.id
                            ? theme.colorScheme.onPrimary
                            : theme.colorScheme.onSurface,
                      ),
                      selectedColor: theme.colorScheme.primary,
                      backgroundColor: theme.colorScheme.surface,
                      side: BorderSide(
                        color: categoryId == item.id
                            ? Colors.transparent
                            : theme.colorScheme.outlineVariant.withAlpha(140),
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                      onSelected: (_) => setState(() => categoryId = item.id),
                    ),
                    const SizedBox(width: 8),
                  ],
                ],
              ),
            ),

            const SizedBox(height: 18),

            // Articles or Empty State
            if (articles.isEmpty)
              Container(
                margin: const EdgeInsets.only(top: 10),
                padding: const EdgeInsets.symmetric(
                  vertical: 36,
                  horizontal: 24,
                ),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surface,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: theme.colorScheme.outlineVariant.withAlpha(120),
                  ),
                ),
                child: Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHighest.withAlpha(120),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        Icons.search_off_rounded,
                        size: 36,
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: 14),
                    Text(
                      'Tidak ada panduan ditemukan',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Coba ubah kata kunci pencarian atau pilih kategori lain.',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    if (query.isNotEmpty || categoryId != null) ...[
                      const SizedBox(height: 16),
                      OutlinedButton.icon(
                        onPressed: () {
                          _searchController.clear();
                          setState(() {
                            query = '';
                            categoryId = null;
                          });
                        },
                        icon: const Icon(Icons.refresh_rounded, size: 18),
                        label: const Text('Reset Pencarian'),
                      ),
                    ],
                  ],
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
        ),
      ),
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
    final theme = Theme.of(context);
    final translation = article.translation(locale);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Detail Panduan'),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        children: [
          // Category and read time header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer.withAlpha(180),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _getCategoryIcon(category.id),
                      size: 13,
                      color: theme.colorScheme.onPrimaryContainer,
                    ),
                    const SizedBox(width: 5),
                    Text(
                      category.label(locale),
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: theme.colorScheme.onPrimaryContainer,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.schedule_rounded,
                    size: 13,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    _estimateReadingTime(translation),
                    style: TextStyle(
                      fontSize: 12,
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 14),

          // Article Title
          Text(
            translation.title,
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w900,
              height: 1.25,
              letterSpacing: -0.3,
            ),
          ),

          const SizedBox(height: 16),

          // Summary Callout Box
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer.withAlpha(70),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: theme.colorScheme.primary.withAlpha(50),
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Icon(
                    Icons.info_outline_rounded,
                    size: 20,
                    color: theme.colorScheme.primary,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    translation.summary,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w500,
                      height: 1.5,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 20),
          Divider(
            height: 1,
            color: theme.colorScheme.outlineVariant.withAlpha(80),
          ),
          const SizedBox(height: 20),

          // Content Blocks
          for (final block in translation.blocks) ...[
            _GuideBlockView(
              block: block,
              mediaPath: mediaPaths[block.mediaId],
            ),
            const SizedBox(height: 16),
          ],

          const SizedBox(height: 12),

          // Safety Reminder Footer
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withAlpha(100),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: theme.colorScheme.outlineVariant.withAlpha(80),
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.health_and_safety_outlined,
                  size: 22,
                  color: theme.colorScheme.primary,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Pemberitahuan Penting',
                        style: theme.textTheme.labelLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Panduan ini merupakan sarana edukasi awal. Jika sapi menunjukkan gejala sakit berat atau darurat, segera hubungi dokter hewan atau petugas kesehatan hewan setempat.',
                        style: theme.textTheme.bodySmall?.copyWith(
                          height: 1.4,
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 32),
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
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return switch (block.type) {
      'heading' => Padding(
          padding: const EdgeInsets.only(top: 8, bottom: 4),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Container(
                width: 4,
                height: 20,
                margin: const EdgeInsets.only(right: 8),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              Expanded(
                child: Text(
                  block.text!,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                    fontSize: 18,
                  ),
                ),
              ),
            ],
          ),
        ),
      'paragraph' => Text(
          block.text!,
          style: theme.textTheme.bodyLarge?.copyWith(
            height: 1.6,
            color: theme.colorScheme.onSurface.withAlpha(230),
          ),
        ),
      'bullet_list' => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final item in block.items!)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(top: 7, right: 10, left: 4),
                      child: Container(
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(
                          color: theme.colorScheme.primary,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                    Expanded(
                      child: Text(
                        item,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          height: 1.55,
                          color: theme.colorScheme.onSurface.withAlpha(230),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      'image' when mediaPath != null => Container(
          margin: const EdgeInsets.symmetric(vertical: 6),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withAlpha(15),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Semantics(
                  image: true,
                  label: block.alt,
                  child: Image.file(File(mediaPath!), fit: BoxFit.cover),
                ),
                if (block.alt != null && block.alt!.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 8,
                    ),
                    color: theme.colorScheme.surfaceContainerHighest.withAlpha(120),
                    child: Text(
                      block.alt!,
                      style: theme.textTheme.bodySmall?.copyWith(
                        fontStyle: FontStyle.italic,
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
              ],
            ),
          ),
        ),
      'image' => Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withAlpha(120),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            children: [
              Icon(
                Icons.broken_image_outlined,
                size: 20,
                color: theme.colorScheme.onSurfaceVariant,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  block.alt ?? 'Gambar panduan tidak tersedia',
                  style: TextStyle(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
            ],
          ),
        ),
      _ => const SizedBox.shrink(),
    };
  }
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
    final theme = Theme.of(context);
    final translation = article.translation(locale);

    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: theme.colorScheme.outlineVariant.withAlpha(120),
        ),
      ),
      color: theme.colorScheme.surface,
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
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primaryContainer.withAlpha(180),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          _getCategoryIcon(category.id),
                          size: 13,
                          color: theme.colorScheme.onPrimaryContainer,
                        ),
                        const SizedBox(width: 5),
                        Text(
                          category.label(locale),
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: theme.colorScheme.onPrimaryContainer,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.schedule_rounded,
                        size: 13,
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _estimateReadingTime(translation),
                        style: TextStyle(
                          fontSize: 12,
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                translation.title,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                  height: 1.3,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 6),
              Text(
                translation.summary,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                  height: 1.45,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Text(
                    'Baca panduan',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Icon(
                    Icons.arrow_forward_rounded,
                    size: 15,
                    color: theme.colorScheme.primary,
                  ),
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
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: theme.colorScheme.primaryContainer.withAlpha(180),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: theme.colorScheme.onPrimaryContainer,
          ),
        ),
      ),
    );
  }
}

IconData _getCategoryIcon(String categoryId) {
  final id = categoryId.toLowerCase();
  if (id.contains('pmk') || id.contains('penyakit') || id.contains('disease')) {
    return Icons.healing_rounded;
  }
  if (id.contains('guna') || id.contains('app') || id.contains('aplikasi')) {
    return Icons.smartphone_rounded;
  }
  if (id.contains('sehat') || id.contains('rawat') || id.contains('health')) {
    return Icons.pets_rounded;
  }
  return Icons.menu_book_rounded;
}

String _estimateReadingTime(GuideTranslation translation) {
  int wordCount =
      translation.title.split(' ').length + translation.summary.split(' ').length;
  for (final b in translation.blocks) {
    if (b.text != null) wordCount += b.text!.split(' ').length;
    if (b.items != null) {
      for (final it in b.items!) {
        wordCount += it.split(' ').length;
      }
    }
  }
  final minutes = (wordCount / 100).ceil();
  return '$minutes mnt baca';
}
