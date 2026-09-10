import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as image;
import 'package:sapisehat_mobile/main.dart';

class _GuideTransport implements ApiTransport {
  _GuideTransport(this.responses);
  final Map<String, ApiResponse> responses;
  final List<String> requests = [];
  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request.path);
    return responses[request.path] ?? ApiResponse(500, '{}');
  }
}

Map<String, dynamic> _descriptor(
  String kind,
  Map<String, dynamic> document,
  int version,
) {
  final bytes = utf8.encode(canonicalJson(document));
  return {
    'id': document['id'],
    'sha256': sha256.convert(bytes).toString(),
    'url': '/api/guide/documents/$kind/${document['id']}?version=$version',
  };
}

List<int> get _validPng => image.encodePng(image.Image(width: 2, height: 2));

AccountSession get _session => AccountSession(
  token: 'token',
  farmerId: 'farmer-1',
  email: 'farmer@example.com',
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'bundled Guide Catalog preserves all six legacy articles and stable IDs',
    () async {
      final raw = await rootBundle.loadString('assets/guide/catalog.json');
      final catalog = GuideCatalog.fromJson(
        jsonDecode(raw) as Map<String, dynamic>,
      );
      expect(catalog.articles, hasLength(6));
      expect(catalog.articles.map((item) => item.id).toSet(), hasLength(6));
      final allText = raw.toLowerCase();
      expect(allText, contains('jarak 1-2 meter'));
      expect(allText, contains('pencahayaan cukup'));
      expect(allText, contains('vaksinasi sesuai arahan'));
      expect(allText, contains('bulu dan kulit bersih'));
      expect(
        catalog.articles.first.translation('en').title,
        catalog.articles.first.translation('id').title,
      );
    },
  );

  test(
    'successful delta activates complete snapshot and restart loads it offline',
    () async {
      final root = await Directory.systemTemp.createTemp('guide-delta');
      final bundled = GuideCatalog.fromJson(
        jsonDecode(await rootBundle.loadString('assets/guide/catalog.json'))
            as Map<String, dynamic>,
      );
      final category = {
        'id': 'guide-category-umum',
        'state': 'active',
        'system_owned': true,
        'display_order': 0,
        'translations': [
          {'locale': 'id', 'label': 'Umum'},
        ],
      };
      final article = {
        'id': 'guide-article-new',
        'category_id': 'guide-category-umum',
        'state': 'published',
        'published_at': '2026-02-01T00:00:00+00:00',
        'translations': [
          {
            'locale': 'id',
            'title': 'Baru',
            'summary': 'Ringkas',
            'blocks': [
              {'type': 'heading', 'text': 'Judul'},
              {'type': 'paragraph', 'text': 'Isi'},
              {
                'type': 'bullet_list',
                'items': ['Satu'],
              },
            ],
          },
        ],
      };
      final manifest = {
        'changed': true,
        'version': 1,
        'documents': {
          'categories': [_descriptor('categories', category, 1)],
          'articles': [_descriptor('articles', article, 1)],
        },
        'media': [],
        'changed_document_ids': [category['id'], article['id']],
        'changed_media_ids': [],
        'removed_document_ids': [],
        'removed_media_ids': [],
      };
      final transport = _GuideTransport({
        '/api/guide/manifest?version=0': ApiResponse(200, jsonEncode(manifest)),
        (manifest['documents'] as Map<String, dynamic>)['categories'][0]['url']:
            ApiResponse(200, canonicalJson(category)),
        (manifest['documents'] as Map<String, dynamic>)['articles'][0]['url']:
            ApiResponse(200, canonicalJson(article)),
      });
      final store = GuideCatalogStore(transport: transport, rootOverride: root);
      final refreshed = await store.refresh(_session, bundled);
      expect(refreshed.version, 1);
      expect(
        refreshed.articles.single.translation('id').blocks.map((b) => b.type),
        ['heading', 'paragraph', 'bullet_list'],
      );
      expect((await store.load()).articles.single.id, 'guide-article-new');
      expect(await File('${root.path}/active').readAsString(), '1');
      await root.delete(recursive: true);
    },
  );

  test('media must match its hash and decode before activation', () async {
    final bundled = GuideCatalog.fromJson(
      jsonDecode(await rootBundle.loadString('assets/guide/catalog.json'))
          as Map<String, dynamic>,
    );
    Future<void> runCase(List<int> bytes, String digest, String suffix) async {
      final root = await Directory.systemTemp.createTemp('guide-media-$suffix');
      final category = {
        'id': 'guide-category-umum',
        'state': 'active',
        'system_owned': true,
        'display_order': 0,
        'translations': [
          {'locale': 'id', 'label': 'Umum'},
        ],
      };
      final article = {
        'id': 'guide-article-image',
        'category_id': 'guide-category-umum',
        'state': 'published',
        'published_at': '2026-02-01T00:00:00+00:00',
        'translations': [
          {
            'locale': 'id',
            'title': 'Gambar',
            'summary': 'Ringkas',
            'blocks': [
              {'type': 'image', 'media_id': 'media-1', 'alt': 'Sapi sehat'},
            ],
          },
        ],
      };
      final manifest = {
        'changed': true,
        'version': 3,
        'documents': {
          'categories': [_descriptor('categories', category, 3)],
          'articles': [_descriptor('articles', article, 3)],
        },
        'media': [
          {
            'id': 'media-1',
            'sha256': digest,
            'mime_type': 'image/png',
            'byte_size': bytes.length,
            'width': 2,
            'height': 2,
            'url': '/media-1',
          },
        ],
        'changed_document_ids': [category['id'], article['id']],
        'changed_media_ids': ['media-1'],
        'removed_document_ids': [],
        'removed_media_ids': [],
      };
      final transport = _GuideTransport({
        '/api/guide/manifest?version=0': ApiResponse(200, jsonEncode(manifest)),
        (manifest['documents'] as Map<String, dynamic>)['categories'][0]['url']:
            ApiResponse(200, canonicalJson(category)),
        (manifest['documents'] as Map<String, dynamic>)['articles'][0]['url']:
            ApiResponse(200, canonicalJson(article)),
        '/media-1': ApiResponse(200, '', bytes: bytes),
      });
      final store = GuideCatalogStore(transport: transport, rootOverride: root);
      if (suffix == 'valid') {
        expect(
          (await store.refresh(_session, bundled)).mediaPaths,
          contains('media-1'),
        );
        expect(await File('${root.path}/active').readAsString(), '3');
      } else {
        await expectLater(
          store.refresh(_session, bundled),
          throwsFormatException,
        );
        expect((await store.load()).version, 0);
        expect(await Directory('${root.path}/candidate-3').exists(), isFalse);
      }
      await root.delete(recursive: true);
    }

    final png = _validPng;
    await runCase(png, sha256.convert(png).toString(), 'valid');
    await runCase(png, '0' * 64, 'bad-hash');
    final invalid = utf8.encode('not an image');
    await runCase(invalid, sha256.convert(invalid).toString(), 'bad-decode');
  });

  test('unchanged documents and media are reused without downloads', () async {
    final root = await Directory.systemTemp.createTemp('guide-reuse');
    final category = {
      'id': 'guide-category-umum',
      'state': 'active',
      'system_owned': true,
      'display_order': 0,
      'translations': [
        {'locale': 'id', 'label': 'Umum'},
      ],
    };
    final article = {
      'id': 'guide-article-image',
      'category_id': 'guide-category-umum',
      'state': 'published',
      'published_at': '2026-02-01T00:00:00+00:00',
      'translations': [
        {
          'locale': 'id',
          'title': 'Gambar',
          'summary': 'Ringkas',
          'blocks': [
            {'type': 'image', 'media_id': 'media-1', 'alt': 'Sapi'},
          ],
        },
      ],
    };
    final png = _validPng;
    final documents = {
      'categories': [_descriptor('categories', category, 1)],
      'articles': [_descriptor('articles', article, 1)],
    };
    final media = {
      'id': 'media-1',
      'sha256': sha256.convert(png).toString(),
      'mime_type': 'image/png',
      'byte_size': png.length,
      'width': 2,
      'height': 2,
      'url': '/media-1',
    };
    final initial = {
      'changed': true,
      'version': 1,
      'documents': documents,
      'media': [media],
      'changed_document_ids': [category['id'], article['id']],
      'changed_media_ids': ['media-1'],
      'removed_document_ids': [],
      'removed_media_ids': [],
    };
    final firstTransport = _GuideTransport({
      '/api/guide/manifest?version=0': ApiResponse(200, jsonEncode(initial)),
      (documents['categories']![0])['url']: ApiResponse(
        200,
        canonicalJson(category),
      ),
      (documents['articles']![0])['url']: ApiResponse(
        200,
        canonicalJson(article),
      ),
      '/media-1': ApiResponse(200, '', bytes: png),
    });
    final firstStore = GuideCatalogStore(
      transport: firstTransport,
      rootOverride: root,
    );
    final active = await firstStore.refresh(
      _session,
      GuideCatalog.fromJson(
        jsonDecode(await rootBundle.loadString('assets/guide/catalog.json'))
            as Map<String, dynamic>,
      ),
    );
    final nextDocuments = {
      'categories': [_descriptor('categories', category, 2)],
      'articles': [_descriptor('articles', article, 2)],
    };
    final second = {
      ...initial,
      'version': 2,
      'documents': nextDocuments,
      'changed_document_ids': <String>[],
      'changed_media_ids': <String>[],
    };
    final secondTransport = _GuideTransport({
      '/api/guide/manifest?version=1': ApiResponse(200, jsonEncode(second)),
    });
    final refreshed = await GuideCatalogStore(
      transport: secondTransport,
      rootOverride: root,
    ).refresh(_session, active);
    expect(refreshed.version, 2);
    expect(secondTransport.requests, ['/api/guide/manifest?version=1']);
    expect(refreshed.mediaPaths, contains('media-1'));
    await root.delete(recursive: true);
  });

  test(
    'bad document hash and interrupted activation retain old snapshot',
    () async {
      final root = await Directory.systemTemp.createTemp('guide-failed');
      final bundled = GuideCatalog.fromJson(
        jsonDecode(await rootBundle.loadString('assets/guide/catalog.json'))
            as Map<String, dynamic>,
      );
      final descriptor = {'id': 'bad', 'sha256': '0' * 64, 'url': '/bad'};
      final manifest = {
        'changed': true,
        'version': 2,
        'documents': {
          'categories': [descriptor],
          'articles': [],
        },
        'media': [],
        'changed_document_ids': ['bad'],
        'changed_media_ids': [],
      };
      final transport = _GuideTransport({
        '/api/guide/manifest?version=0': ApiResponse(200, jsonEncode(manifest)),
        '/bad': ApiResponse(200, '{}'),
      });
      final store = GuideCatalogStore(transport: transport, rootOverride: root);
      await expectLater(
        store.refresh(_session, bundled),
        throwsFormatException,
      );
      expect((await store.load()).version, 0);
      expect(await Directory('${root.path}/candidate-2').exists(), isFalse);
      await root.delete(recursive: true);
    },
  );
}
