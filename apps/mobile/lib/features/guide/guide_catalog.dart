import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';
import 'package:image/image.dart' as image;
import 'package:path_provider/path_provider.dart';

import '../../core/api.dart';
import '../auth/auth.dart';

class GuideCategory {
  const GuideCategory({
    required this.id,
    required this.labels,
    required this.order,
  });
  final String id;
  final Map<String, String> labels;
  final int order;
  String label(String locale) => labels[locale] ?? labels['id'] ?? 'Umum';
  factory GuideCategory.fromJson(Map<String, dynamic> json) => GuideCategory(
    id: json['id'] as String,
    order: json['display_order'] as int? ?? 0,
    labels: {
      for (final raw in json['translations'] as List<dynamic>)
        (raw as Map<String, dynamic>)['locale'] as String:
            raw['label'] as String,
    },
  );
}

class GuideBlock {
  const GuideBlock({
    required this.type,
    this.text,
    this.items,
    this.mediaId,
    this.alt,
  });
  final String type;
  final String? text;
  final List<String>? items;
  final String? mediaId;
  final String? alt;
  factory GuideBlock.fromJson(Map<String, dynamic> json) {
    const types = {'heading', 'paragraph', 'bullet_list', 'image'};
    final type = json['type'] as String;
    if (!types.contains(type)) {
      throw const FormatException('Unknown Guide block');
    }
    return GuideBlock(
      type: type,
      text: json['text'] as String?,
      items: (json['items'] as List<dynamic>?)?.cast<String>(),
      mediaId: json['media_id'] as String?,
      alt: json['alt'] as String?,
    );
  }
}

class GuideTranslation {
  const GuideTranslation({
    required this.title,
    required this.summary,
    required this.blocks,
  });
  final String title;
  final String summary;
  final List<GuideBlock> blocks;
}

class GuideArticle {
  const GuideArticle({
    required this.id,
    required this.categoryId,
    required this.publishedAt,
    required this.translations,
  });
  final String id;
  final String categoryId;
  final DateTime publishedAt;
  final Map<String, GuideTranslation> translations;
  GuideTranslation translation(String locale) =>
      translations[locale] ?? translations['id']!;
  factory GuideArticle.fromJson(Map<String, dynamic> json) {
    final translations = <String, GuideTranslation>{
      for (final raw in json['translations'] as List<dynamic>)
        (raw as Map<String, dynamic>)['locale'] as String: GuideTranslation(
          title: raw['title'] as String,
          summary: raw['summary'] as String,
          blocks: (raw['blocks'] as List<dynamic>)
              .map(
                (block) => GuideBlock.fromJson(block as Map<String, dynamic>),
              )
              .toList(),
        ),
    };
    if (!translations.containsKey('id')) {
      throw const FormatException(
        'Bahasa Indonesia Guide translation required',
      );
    }
    return GuideArticle(
      id: json['id'] as String,
      categoryId: json['category_id'] as String,
      publishedAt: DateTime.parse(json['published_at'] as String),
      translations: translations,
    );
  }
}

class GuideCatalog {
  const GuideCatalog({
    required this.version,
    required this.categories,
    required this.articles,
    required this.mediaPaths,
    required this.filePaths,
  });
  final int version;
  final List<GuideCategory> categories;
  final List<GuideArticle> articles;
  final Map<String, String> mediaPaths;
  final Map<String, String> filePaths;
  factory GuideCatalog.fromJson(
    Map<String, dynamic> json, {
    Map<String, String> mediaPaths = const {},
    Map<String, String> filePaths = const {},
  }) {
    final documents = json['documents'] as Map<String, dynamic>;
    final categories = (documents['categories'] as List<dynamic>)
        .map((item) => GuideCategory.fromJson(item as Map<String, dynamic>))
        .toList();
    final articles = (documents['articles'] as List<dynamic>)
        .map((item) => GuideArticle.fromJson(item as Map<String, dynamic>))
        .toList();
    final categoryIds = categories.map((item) => item.id).toSet();
    if (categoryIds.length != categories.length ||
        articles.map((item) => item.id).toSet().length != articles.length ||
        articles.any((item) => !categoryIds.contains(item.categoryId))) {
      throw const FormatException('Incomplete Guide membership');
    }
    final mediaIds = (json['media'] as List<dynamic>? ?? const [])
        .map((item) => (item as Map<String, dynamic>)['id'] as String)
        .toSet();
    if (articles
        .expand((item) => item.translations.values)
        .expand((item) => item.blocks)
        .where((item) => item.type == 'image')
        .any((item) => !mediaIds.contains(item.mediaId))) {
      throw const FormatException('Missing Guide media membership');
    }
    return GuideCatalog(
      version: json['version'] as int? ?? 0,
      categories: categories,
      articles: articles,
      mediaPaths: mediaPaths,
      filePaths: filePaths,
    );
  }
}

String canonicalJson(Object? value) {
  if (value is Map) {
    final keys = value.keys.cast<String>().toList()..sort();
    return '{${keys.map((key) => '${jsonEncode(key)}:${canonicalJson(value[key])}').join(',')}}';
  }
  if (value is List) return '[${value.map(canonicalJson).join(',')}]';
  return jsonEncode(value);
}

class GuideCatalogStore {
  GuideCatalogStore({
    ApiTransport? transport,
    this.rootOverride,
    this.beforeActivate,
  }) : transport = transport ?? HttpApiTransport();
  final ApiTransport transport;
  final Directory? rootOverride;
  final Future<void> Function()? beforeActivate;
  Future<Directory> _root() async =>
      rootOverride ??
      Directory('${(await getApplicationSupportDirectory()).path}/guide');

  Future<GuideCatalog> load() async {
    final root = await _root();
    final pointer = File('${root.path}/active');
    if (await pointer.exists()) {
      try {
        final version = (await pointer.readAsString()).trim();
        return await _loadSnapshot(Directory('${root.path}/$version'));
      } catch (_) {
        // A corrupt retained snapshot never replaces the bundled fallback.
      }
    }
    return GuideCatalog.fromJson(
      jsonDecode(await rootBundle.loadString('assets/guide/catalog.json'))
          as Map<String, dynamic>,
    );
  }

  Future<GuideCatalog> _loadSnapshot(Directory directory) async {
    final manifest =
        jsonDecode(await File('${directory.path}/catalog.json').readAsString())
            as Map<String, dynamic>;
    final documents = <String, dynamic>{
      'categories': <dynamic>[],
      'articles': <dynamic>[],
    };
    final filePaths = <String, String>{};
    for (final kind in ['categories', 'articles']) {
      for (final raw
          in (manifest['documents'] as Map<String, dynamic>)[kind]
              as List<dynamic>) {
        final descriptor = raw as Map<String, dynamic>;
        final file = File(
          '${directory.path}/documents/$kind/${descriptor['id']}.json',
        );
        final bytes = await file.readAsBytes();
        _verify(bytes, descriptor['sha256'] as String);
        (documents[kind] as List<dynamic>).add(jsonDecode(utf8.decode(bytes)));
        filePaths['$kind:${descriptor['id']}'] = file.path;
      }
    }
    final mediaPaths = <String, String>{};
    final mediaIds = <String>{};
    for (final raw in manifest['media'] as List<dynamic>? ?? const []) {
      final descriptor = raw as Map<String, dynamic>;
      final id = descriptor['id'] as String;
      if (!mediaIds.add(id)) {
        throw const FormatException('Duplicate Guide media membership');
      }
      final file = File('${directory.path}/media/$id');
      final bytes = await file.readAsBytes();
      _verify(bytes, descriptor['sha256'] as String);
      _decodeImage(bytes);
      mediaPaths[id] = file.path;
    }
    final directoryVersion = int.tryParse(directory.path.split('/').last);
    if (directoryVersion != null && manifest['version'] != directoryVersion) {
      throw const FormatException('Guide snapshot version mismatch');
    }
    return GuideCatalog.fromJson(
      {
        'version': manifest['version'],
        'documents': documents,
        'media': manifest['media'] ?? [],
      },
      mediaPaths: mediaPaths,
      filePaths: filePaths,
    );
  }

  Future<GuideCatalog> refresh(
    AccountSession session,
    GuideCatalog active,
  ) async {
    final manifestResponse = await _request(
      '/api/guide/manifest?version=${active.version}',
      session.token,
    );
    final manifest = manifestResponse.json;
    if (manifest['changed'] == false) return active;
    final version = manifest['version'] as int;
    final root = await _root();
    final candidate = Directory('${root.path}/candidate-$version');
    if (await candidate.exists()) await candidate.delete(recursive: true);
    await candidate.create(recursive: true);
    try {
      final changedDocuments =
          (manifest['changed_document_ids'] as List<dynamic>? ?? const [])
              .cast<String>()
              .toSet();
      final changedMedia =
          (manifest['changed_media_ids'] as List<dynamic>? ?? const [])
              .cast<String>()
              .toSet();
      for (final kind in ['categories', 'articles']) {
        for (final raw
            in (manifest['documents'] as Map<String, dynamic>)[kind]
                as List<dynamic>) {
          final descriptor = raw as Map<String, dynamic>;
          final id = descriptor['id'] as String;
          final destination = File(
            '${candidate.path}/documents/$kind/$id.json',
          );
          await destination.parent.create(recursive: true);
          final existingPath = active.filePaths['$kind:$id'];
          if (!changedDocuments.contains(id) &&
              existingPath != null &&
              await _copyVerified(
                File(existingPath),
                destination,
                descriptor['sha256'] as String,
              )) {
            continue;
          }
          final response = await _request(
            descriptor['url'] as String,
            session.token,
          );
          _verify(response.bytes, descriptor['sha256'] as String);
          jsonDecode(utf8.decode(response.bytes));
          await destination.writeAsBytes(response.bytes, flush: true);
        }
      }
      for (final raw in manifest['media'] as List<dynamic>? ?? const []) {
        final descriptor = raw as Map<String, dynamic>;
        final id = descriptor['id'] as String;
        final destination = File('${candidate.path}/media/$id');
        await destination.parent.create(recursive: true);
        final existingPath = active.mediaPaths[id];
        if (!changedMedia.contains(id) &&
            existingPath != null &&
            await _copyVerified(
              File(existingPath),
              destination,
              descriptor['sha256'] as String,
            )) {
          continue;
        }
        final response = await _request(
          descriptor['url'] as String,
          session.token,
        );
        _verify(response.bytes, descriptor['sha256'] as String);
        await destination.writeAsBytes(response.bytes, flush: true);
      }
      await File(
        '${candidate.path}/catalog.json',
      ).writeAsString(jsonEncode(manifest), flush: true);
      await _loadSnapshot(candidate);
      if (beforeActivate != null) await beforeActivate!();
      final finalDirectory = Directory('${root.path}/$version');
      if (await finalDirectory.exists()) {
        await finalDirectory.delete(recursive: true);
      }
      await candidate.rename(finalDirectory.path);
      await root.create(recursive: true);
      final temporaryPointer = File('${root.path}/active.tmp');
      await temporaryPointer.writeAsString('$version', flush: true);
      await temporaryPointer.rename('${root.path}/active');
      return await _loadSnapshot(finalDirectory);
    } catch (_) {
      if (await candidate.exists()) await candidate.delete(recursive: true);
      rethrow;
    }
  }

  Future<ApiResponse> _request(String path, String token) async {
    final response = await transport.send(
      ApiRequest(
        'GET',
        path,
        headers: {
          'Accept': 'application/json',
          'Authorization': 'Bearer $token',
        },
      ),
    );
    if (response.statusCode != 200) {
      throw const FileSystemException('Guide download failed');
    }
    return response;
  }

  Future<bool> _copyVerified(
    File source,
    File destination,
    String digest,
  ) async {
    if (!await source.exists()) return false;
    final bytes = await source.readAsBytes();
    if (sha256.convert(bytes).toString() != digest) return false;
    await destination.writeAsBytes(bytes, flush: true);
    return true;
  }

  void _verify(List<int> bytes, String digest) {
    if (sha256.convert(bytes).toString() != digest) {
      throw const FormatException('Guide SHA-256 mismatch');
    }
  }

  void _decodeImage(List<int> bytes) {
    if (image.decodeImage(Uint8List.fromList(bytes)) == null) {
      throw const FormatException('Guide media decode failed');
    }
  }
}
