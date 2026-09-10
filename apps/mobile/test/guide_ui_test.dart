import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/features/guide/guide_catalog.dart';
import 'package:sapisehat_mobile/features/guide/guide_screen.dart';

void main() {
  final category = GuideCategory(
    id: 'pmk',
    labels: {'id': 'PMK', 'en': 'FMD'},
    order: 10,
  );

  final article = GuideArticle(
    id: 'art-1',
    categoryId: 'pmk',
    publishedAt: DateTime(2026, 3, 1),
    translations: {
      'id': GuideTranslation(
        title: 'Gejala dan Pencegahan PMK',
        summary: 'Panduan lengkap mengenali gejala awal dan pencegahan PMK.',
        blocks: [
          const GuideBlock(type: 'heading', text: 'Gejala Klinis'),
          const GuideBlock(
            type: 'paragraph',
            text: 'Sapi yang terinfeksi PMK biasanya mengalami demam tinggi.',
          ),
          const GuideBlock(
            type: 'bullet_list',
            items: ['Air liur berlebihan', 'Luka pada teracak kuku'],
          ),
          const GuideBlock(
            type: 'image',
            alt: 'Ilustrasi pemeriksaan',
          ),
        ],
      ),
    },
  );

  testWidgets('GuideArticleCard renders category, read time, title, and summary', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: GuideArticleCard(
            article: article,
            category: category,
            locale: 'id',
            mediaPaths: const {},
          ),
        ),
      ),
    );

    expect(find.text('PMK'), findsOneWidget);
    expect(find.text('Gejala dan Pencegahan PMK'), findsOneWidget);
    expect(
      find.text('Panduan lengkap mengenali gejala awal dan pencegahan PMK.'),
      findsOneWidget,
    );
    expect(find.text('Baca panduan'), findsOneWidget);
    expect(find.byIcon(Icons.arrow_forward_rounded), findsOneWidget);
  });

  testWidgets('GuideDetailPage renders header, callout, blocks, and disclaimer', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: GuideDetailPage(
          article: article,
          category: category,
          locale: 'id',
          mediaPaths: const {},
        ),
      ),
    );

    expect(find.text('Detail Panduan'), findsOneWidget);
    expect(find.text('PMK'), findsOneWidget);
    expect(find.text('Gejala dan Pencegahan PMK'), findsOneWidget);
    expect(
      find.text('Panduan lengkap mengenali gejala awal dan pencegahan PMK.'),
      findsOneWidget,
    );
    expect(find.byIcon(Icons.info_outline_rounded), findsOneWidget);
    expect(find.text('Gejala Klinis'), findsOneWidget);
    expect(find.text('Air liur berlebihan'), findsOneWidget);
    expect(find.text('Pemberitahuan Penting'), findsOneWidget);
  });
}
