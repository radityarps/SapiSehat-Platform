import 'package:flutter/material.dart';

class GuideScreen extends StatefulWidget {
  const GuideScreen({super.key});

  @override
  State<GuideScreen> createState() => _GuideScreenState();
}

class _GuideScreenState extends State<GuideScreen> {
  String query = '';
  GuideCategory? category;

  List<GuideArticle> get articles {
    final q = query.trim().toLowerCase();
    return guideArticles.where((a) {
      final matchCategory = category == null || a.category == category;
      final matchQuery =
          q.isEmpty ||
          a.title.toLowerCase().contains(q) ||
          a.summary.toLowerCase().contains(q) ||
          a.body.toLowerCase().contains(q);
      return matchCategory && matchQuery;
    }).toList();
  }

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(20),
    children: [
      Text(
        'Panduan',
        style: Theme.of(
          context,
        ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
      ),
      const SizedBox(height: 8),
      const Text('Panduan penggunaan aplikasi, PMK, LSD, dan sapi sehat.'),
      const SizedBox(height: 16),
      TextField(
        decoration: const InputDecoration(
          labelText: 'Cari panduan',
          hintText: 'Cari PMK, LSD, scan, biosekuriti...',
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
                selected: category == null,
                label: const Text('Semua'),
                onSelected: (_) => setState(() => category = null),
              ),
            ),
            for (final item in GuideCategory.values)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: FilterChip(
                  selected: category == item,
                  label: Text(item.label),
                  onSelected: (_) => setState(() => category = item),
                ),
              ),
          ],
        ),
      ),
      if (query.isNotEmpty || category != null) ...[
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            onPressed: () => setState(() {
              query = '';
              category = null;
            }),
            icon: const Icon(Icons.clear),
            label: const Text('Hapus filter'),
          ),
        ),
      ],
      const SizedBox(height: 16),
      if (articles.isEmpty)
        const Card(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Text('Tidak ada panduan ditemukan'),
          ),
        )
      else
        for (final article in articles) GuideArticleCard(article: article),
    ],
  );
}

class GuideDetailPage extends StatelessWidget {
  const GuideDetailPage({super.key, required this.article});
  final GuideArticle article;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Panduan')),
    body: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Align(
          alignment: Alignment.centerLeft,
          child: GuideBadge(category: article.category),
        ),
        const SizedBox(height: 14),
        Text(
          article.title,
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 10),
        Text(article.summary),
        const SizedBox(height: 18),
        for (final block in article.body.split('\n\n')) ...[
          Text(block, style: const TextStyle(height: 1.45)),
          const SizedBox(height: 14),
        ],
      ],
    ),
  );
}

class GuideArticleCard extends StatelessWidget {
  const GuideArticleCard({super.key, required this.article});
  final GuideArticle article;

  @override
  Widget build(BuildContext context) => Card(
    clipBehavior: Clip.antiAlias,
    child: InkWell(
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => GuideDetailPage(article: article)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              article.title,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 6),
            Text(article.summary),
            const SizedBox(height: 12),
            Row(
              children: [
                Text(
                  'Baca ->',
                  style: TextStyle(
                    color: article.category.color,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const Spacer(),
                GuideBadge(category: article.category),
              ],
            ),
          ],
        ),
      ),
    ),
  );
}

class GuideBadge extends StatelessWidget {
  const GuideBadge({super.key, required this.category});
  final GuideCategory category;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
    decoration: BoxDecoration(
      color: category.color.withValues(alpha: 0.12),
      borderRadius: BorderRadius.circular(999),
      border: Border.all(color: category.color.withValues(alpha: 0.28)),
    ),
    child: Text(
      category.label,
      style: TextStyle(
        color: category.color,
        fontWeight: FontWeight.w800,
        fontSize: 12,
      ),
    ),
  );
}

class GuideArticle {
  const GuideArticle({
    required this.category,
    required this.title,
    required this.summary,
    required this.body,
  });
  final GuideCategory category;
  final String title;
  final String summary;
  final String body;
}

enum GuideCategory {
  app('Penggunaan', Color(0xFF2E6B4F)),
  fmd('PMK', Color(0xFFE4572E)),
  lsd('LSD', Color(0xFFF59E0B)),
  healthy('Sapi Sehat', Color(0xFF22A06B));

  const GuideCategory(this.label, this.color);
  final String label;
  final Color color;
}

const guideArticles = [
  GuideArticle(
    category: GuideCategory.app,
    title: 'Memulai Scan Pertama',
    summary:
        'Panduan lengkap menggunakan fitur scan untuk mendeteksi penyakit pada sapi Anda.',
    body:
        'Buka tab Scan, arahkan kamera ke sapi, lalu ambil foto. Gunakan jarak 1-2 meter, pencahayaan cukup, dan posisi sejajar tubuh sapi.\n\nHasil menampilkan sinyal risiko, confidence score, dan saran tindakan awal. Hasil bukan diagnosis dokter hewan.',
  ),
  GuideArticle(
    category: GuideCategory.app,
    title: 'Mode Online vs Offline',
    summary: 'Perbedaan mode inferensi online dan offline.',
    body:
        'Mode online memakai server saat koneksi stabil. Mode offline bekerja di perangkat saat tidak ada sinyal.',
  ),
  GuideArticle(
    category: GuideCategory.fmd,
    title: 'Mengenal PMK',
    summary: 'Informasi dasar Penyakit Mulut dan Kuku.',
    body:
        'PMK menyerang hewan berkuku belah. Gejala umum: demam, air liur berlebih, lepuh mulut, dan pincang.',
  ),
  GuideArticle(
    category: GuideCategory.fmd,
    title: 'Pencegahan PMK',
    summary: 'Biosekuriti dan tindakan awal PMK.',
    body:
        'Isolasi sapi bergejala, batasi lalu lintas kandang, lakukan desinfeksi, vaksinasi sesuai arahan, dan hubungi petugas kesehatan hewan.',
  ),
  GuideArticle(
    category: GuideCategory.lsd,
    title: 'Mengenal LSD',
    summary: 'Informasi dasar Lumpy Skin Disease.',
    body:
        'LSD menyebabkan benjolan kulit pada sapi. Penyakit menyebar terutama lewat nyamuk, lalat penghisap darah, dan caplak.',
  ),
  GuideArticle(
    category: GuideCategory.lsd,
    title: 'Pencegahan LSD',
    summary: 'Pengendalian vektor dan kandang.',
    body:
        'Kendalikan serangga, bersihkan genangan air, semprot kandang, karantina ternak baru, dan laporkan gejala ke petugas.',
  ),
  GuideArticle(
    category: GuideCategory.healthy,
    title: 'Ciri-Ciri Sapi Sehat',
    summary: 'Tanda visual sapi sehat sebagai pembanding.',
    body:
        'Sapi sehat aktif, nafsu makan baik, bulu mengkilap, mata cerah, kulit bersih, dan bergerak normal tanpa pincang.',
  ),
  GuideArticle(
    category: GuideCategory.healthy,
    title: 'Biosekuriti Harian',
    summary: 'Rutinitas menjaga kesehatan ternak.',
    body:
        'Bersihkan kandang, sediakan air bersih, batasi pengunjung, gunakan alas kaki khusus, karantina ternak baru, dan catat kesehatan sapi.',
  ),
];
