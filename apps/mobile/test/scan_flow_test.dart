import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/features/scan/scan_result_detail_page.dart';
import 'package:sapisehat_mobile/main.dart';

class ScanTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/predict') {
      return ApiResponse(
        200,
        jsonEncode({
          'status': 'success',
          'prediction': {
            'disease_class': 'FMD',
            'confidence': 0.82,
            'is_reliable': true,
            'scores': {'FMD': 0.82, 'healthy': 0.18},
          },
          'model_info': {'version': '1.0.0'},
        }),
      );
    }
    if (request.path == '/api/media/uploads') {
      return ApiResponse(
        200,
        jsonEncode({
          'id': 'media-1',
          'farmer_id': 'farmer-1',
          'cattle_id': 'cattle-1',
          'storage_reference': 'scan-images/farmer-1/2026/06/media-1.jpg',
        }),
      );
    }
    if (request.path == '/api/fusion/results') {
      return ApiResponse(
        200,
        jsonEncode({
          'id': 'fusion-1',
          'farmer_id': 'farmer-1',
          'cattle_id': 'cattle-1',
          'disease_class': 'FMD',
          'confidence': 0.82,
          'confidence_level': 'high',
          'reliability': 'reliable',
          'handling_advice_key': 'advice.isolate_and_contact_vet',
          'evidence_breakdown': {},
          'conflict_status': 'none',
          'model_versions': {},
          'created_at': '2026-06-16T00:00:00Z',
        }),
      );
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  test('camera scan classifies image then stores fusion result', () async {
    final transport = ScanTransport();
    final api = SapiSehatApiClient(transport: transport);

    final result = await api.uploadScan(
      farmerId: 'farmer-1',
      cattleId: 'cattle-1',
      bytes: [1, 2, 3, 4],
    );

    expect(result.label, 'FMD');
    expect(result.confidence, 0.82);
    expect(result.inferenceMode, 'online');
    expect(result.syncStatus, 'synced');
    expect(transport.requests.map((request) => request.path), [
      '/api/predict',
      '/api/fusion/results',
    ]);
    expect(transport.requests.first.fileBytes, [1, 2, 3, 4]);
    expect(transport.requests.first.fileField, 'image');
    expect(transport.requests.last.body, contains('image_evidence'));
  });

  testWidgets('scan result opened from scan flow hides edit cow button', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: ScanResultDetailPage(
          apiClient: SapiSehatApiClient(transport: ScanTransport()),
          session: AccountSession(
            token: 'token',
            farmerId: 'farmer-1',
            email: 'farmer@example.com',
          ),
          result: ScanResult(
            localId: 'scan-1',
            label: 'FMD',
            confidence: 0.82,
            capturedAt: DateTime(2026, 6, 16),
            inferenceMode: 'online',
            syncStatus: 'unsaved',
            modelVersion: 'fmd-mobilenetv3-test',
            scores: const {'FMD': 0.82, 'healthy': 0.18},
          ),
          image: null,
          cattle: [
            CattleProfile(
              id: 'cattle-1',
              tag: 'SAPI-001',
              name: 'Mawar',
              status: 'active',
              breed: 'Sapi Bali',
            ),
          ],
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView), const Offset(0, -1200));
    await tester.pumpAndSettle();

    expect(find.text('Edit sapi'), findsNothing);
    expect(find.text('Hapus'), findsOneWidget);
    expect(find.text('Ulangi'), findsOneWidget);
  });

  testWidgets('save dialog shows cow name and tag without separator artifact', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: ScanResultDetailPage(
          apiClient: SapiSehatApiClient(transport: ScanTransport()),
          session: AccountSession(
            token: 'token',
            farmerId: 'farmer-1',
            email: 'farmer@example.com',
          ),
          result: ScanResult(
            localId: 'scan-1',
            label: 'FMD',
            confidence: 0.82,
            capturedAt: DateTime(2026, 6, 16),
            inferenceMode: 'online',
            syncStatus: 'unsaved',
            modelVersion: 'fmd-mobilenetv3-test',
            scores: const {'FMD': 0.82, 'healthy': 0.18},
          ),
          image: null,
          cattle: [
            CattleProfile(
              id: 'cattle-1',
              tag: '002',
              name: 'Sapi Bali',
              status: 'active',
              breed: 'Sapi Bali',
            ),
          ],
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView), const Offset(0, -1200));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Simpan'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Tidak dikaitkan'));
    await tester.pumpAndSettle();

    expect(find.text('Sapi Bali (002)'), findsOneWidget);
    expect(find.textContaining('Â'), findsNothing);
  });

  testWidgets('scan result opened from history keeps edit cow button', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: ScanResultDetailPage(
          apiClient: SapiSehatApiClient(transport: ScanTransport()),
          session: AccountSession(
            token: 'token',
            farmerId: 'farmer-1',
            email: 'farmer@example.com',
          ),
          result: ScanResult(
            localId: 'scan-1',
            label: 'FMD',
            confidence: 0.82,
            capturedAt: DateTime(2026, 6, 16),
            inferenceMode: 'online',
            syncStatus: 'synced',
            modelVersion: 'fmd-mobilenetv3-test',
            scores: const {'FMD': 0.82, 'healthy': 0.18},
          ),
          image: null,
          cattle: [
            CattleProfile(
              id: 'cattle-1',
              tag: 'SAPI-001',
              name: 'Mawar',
              status: 'active',
              breed: 'Sapi Bali',
            ),
          ],
          skipAutoSave: true,
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView), const Offset(0, -1200));
    await tester.pumpAndSettle();

    expect(find.text('Edit sapi'), findsOneWidget);
    expect(find.text('Hapus'), findsOneWidget);
    expect(find.text('Simpan'), findsNothing);
  });

  testWidgets('result detail shows linked cow name and tag after edit', (
    tester,
  ) async {
    var changedTo = '';
    var refreshed = false;
    await tester.pumpWidget(
      MaterialApp(
        home: ScanResultDetailPage(
          apiClient: SapiSehatApiClient(transport: ScanTransport()),
          session: AccountSession(
            token: 'token',
            farmerId: 'farmer-1',
            email: 'farmer@example.com',
          ),
          result: ScanResult(
            localId: 'scan-1',
            cattleId: 'cattle-1',
            label: 'FMD',
            confidence: 0.82,
            capturedAt: DateTime(2026, 6, 16),
            inferenceMode: 'online',
            syncStatus: 'synced',
            modelVersion: 'fmd-mobilenetv3-test',
            scores: const {'FMD': 0.82, 'healthy': 0.18},
          ),
          image: null,
          cattle: [
            CattleProfile(
              id: 'cattle-1',
              tag: '001',
              name: 'Mawar',
              status: 'active',
              breed: 'Sapi Bali',
            ),
            CattleProfile(
              id: 'cattle-2',
              tag: '002',
              name: 'Melati',
              status: 'active',
              breed: 'Sapi Bali',
            ),
          ],
          skipAutoSave: true,
          onChangeCattle: (cattleId) async => changedTo = cattleId!,
          onChanged: () async => refreshed = true,
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView), const Offset(0, -1200));
    await tester.pumpAndSettle();

    expect(find.text('Mawar (001)'), findsOneWidget);
    await tester.tap(find.text('Edit sapi'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Melati'));
    await tester.pumpAndSettle();

    expect(changedTo, 'cattle-2');
    expect(refreshed, isTrue);
    expect(find.text('Melati (002)'), findsOneWidget);
    expect(find.text('Sapi terkait berhasil diperbarui.'), findsOneWidget);
  });

  testWidgets('result detail does not expose missing cattle id', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: ScanResultDetailPage(
          apiClient: SapiSehatApiClient(transport: ScanTransport()),
          session: AccountSession(
            token: 'token',
            farmerId: 'farmer-1',
            email: 'farmer@example.com',
          ),
          result: ScanResult(
            localId: 'scan-1',
            cattleId: 'cattle-missing',
            label: 'FMD',
            confidence: 0.82,
            capturedAt: DateTime(2026, 6, 16),
            inferenceMode: 'online',
            syncStatus: 'synced',
            modelVersion: 'fmd-mobilenetv3-test',
            scores: const {'FMD': 0.82, 'healthy': 0.18},
          ),
          image: null,
          cattle: const [],
          skipAutoSave: true,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Belum dikaitkan'), findsOneWidget);
    expect(find.text('cattle-missing'), findsNothing);
  });

  testWidgets('delete result shows success toast and closes detail page', (
    tester,
  ) async {
    var deleted = false;
    Object? routeResult;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async {
                routeResult = await Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => ScanResultDetailPage(
                      apiClient: SapiSehatApiClient(transport: ScanTransport()),
                      session: AccountSession(
                        token: 'token',
                        farmerId: 'farmer-1',
                        email: 'farmer@example.com',
                      ),
                      result: ScanResult(
                        localId: 'scan-1',
                        label: 'FMD',
                        confidence: 0.82,
                        capturedAt: DateTime(2026, 6, 16),
                        inferenceMode: 'online',
                        syncStatus: 'synced',
                        modelVersion: 'fmd-mobilenetv3-test',
                        scores: const {'FMD': 0.82, 'healthy': 0.18},
                      ),
                      image: null,
                      cattle: const [],
                      skipAutoSave: true,
                      onDelete: () async => deleted = true,
                    ),
                  ),
                );
              },
              child: const Text('Open'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView), const Offset(0, -1200));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Hapus'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Hapus').last);
    await tester.pumpAndSettle();

    expect(deleted, isTrue);
    expect(routeResult, 'deleted');
    expect(find.text('Riwayat berhasil dihapus.'), findsOneWidget);
  });
}
