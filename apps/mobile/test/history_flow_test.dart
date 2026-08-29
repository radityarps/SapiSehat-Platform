import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/features/history/history_screen.dart';
import 'package:sapisehat_mobile/main.dart';

class HistoryTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/fusion/results') {
      return ApiResponse(
        200,
        jsonEncode({
          'results': [
            {
              'id': 'fusion-1',
              'farmer_id': 'farmer-1',
              'cattle_id': 'cattle-1',
              'disease_class': 'FMD',
              'confidence': 0.72,
              'inference_mode': 'synced_offline',
              'created_at': '2026-06-05T08:30:00+07:00',
            },
            {
              'id': 'fusion-other',
              'farmer_id': 'other-farmer',
              'cattle_id': 'cattle-9',
              'disease_class': 'LSD',
              'confidence': 0.61,
              'inference_mode': 'online',
              'created_at': '2026-06-06T08:30:00+07:00',
            },
          ],
        }),
      );
    }
    if (request.path == '/api/farmers/farmer-1/cattle') {
      return ApiResponse(200, jsonEncode({'cattle': []}));
    }
    if (request.path == '/api/fusion/results/fusion-1/cattle' &&
        request.method == 'PATCH') {
      final body = jsonDecode(request.body!);
      return ApiResponse(
        200,
        jsonEncode({
          'id': 'fusion-1',
          'farmer_id': body['farmer_id'],
          'cattle_id': body['cattle_id'],
          'disease_class': 'FMD',
          'confidence': 0.72,
          'inference_mode': 'synced_offline',
          'created_at': '2026-06-05T08:30:00+07:00',
        }),
      );
    }
    if (request.path == '/api/fusion/results/fusion-1?farmer_id=farmer-1' &&
        request.method == 'DELETE') {
      return ApiResponse(200, jsonEncode({'status': 'deleted'}));
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  test(
    'detection history returns farmer-scoped risk signals without diagnosis copy',
    () async {
      final transport = HistoryTransport();
      final api = SapiSehatApiClient(transport: transport);

      final history = await api.listDetectionHistory('farmer-1');

      expect(history.single.id, 'fusion-1');
      expect(history.single.label, 'FMD');
      expect(history.single.safeSummary, 'Risk signal: FMD');
      expect(
        history.single.safeSummary.toLowerCase(),
        isNot(contains('diagnosis')),
      );
      expect(transport.requests.single.path, '/api/fusion/results');
    },
  );

  test(
    'history cattle reassignment patches fusion result association',
    () async {
      final transport = HistoryTransport();
      final api = SapiSehatApiClient(transport: transport);

      await api.updateDetectionHistoryCattle(
        farmerId: 'farmer-1',
        resultId: 'fusion-1',
        cattleId: 'cattle-2',
      );

      expect(transport.requests.single.method, 'PATCH');
      expect(
        transport.requests.single.path,
        '/api/fusion/results/fusion-1/cattle',
      );
      expect(jsonDecode(transport.requests.single.body!), {
        'farmer_id': 'farmer-1',
        'cattle_id': 'cattle-2',
      });
    },
  );

  test('history delete removes fusion result association', () async {
    final transport = HistoryTransport();
    final api = SapiSehatApiClient(transport: transport);

    await api.deleteDetectionHistory(
      farmerId: 'farmer-1',
      resultId: 'fusion-1',
    );

    expect(transport.requests.single.method, 'DELETE');
    expect(
      transport.requests.single.path,
      '/api/fusion/results/fusion-1?farmer_id=farmer-1',
    );
  });

  testWidgets('history shows backend results before synced local cache', (
    tester,
  ) async {
    final api = SapiSehatApiClient(transport: HistoryTransport());
    final image = File('${Directory.systemTemp.path}/history-fusion-1.png')
      ..writeAsBytesSync(
        base64Decode(
          'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/ltnG7wAAAABJRU5ErkJggg==',
        ),
      );

    await tester.pumpWidget(
      MaterialApp(
        home: HistoryScreen(
          apiClient: api,
          session: AccountSession(
            token: 'token',
            farmerId: 'farmer-1',
            email: 'farmer@example.com',
          ),
          localHistory: [
            ScanResult(
              localId: 'fusion-1',
              label: 'FMD',
              confidence: 0.72,
              capturedAt: DateTime(2026, 6, 5, 8, 30),
              inferenceMode: 'online',
              syncStatus: 'synced',
              imagePath: image.path,
              modelVersion: 'fmd-mobilenetv3-test',
              scores: const {'FMD': 0.72, 'healthy': 0.28},
            ),
            ScanResult(
              localId: 'fusion-new',
              label: 'healthy',
              confidence: 0.91,
              capturedAt: DateTime(2026, 6, 6, 9, 30),
              inferenceMode: 'online',
              syncStatus: 'synced',
              modelVersion: 'fmd-mobilenetv3-test',
              scores: const {'FMD': 0.09, 'healthy': 0.91},
            ),
          ],
          onUpdateLocal: (_) {},
          onDeleteLocal: (_) {},
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(ListTile), findsNWidgets(2));
    expect(find.byType(Image), findsOneWidget);
    expect(find.textContaining('FMD'), findsWidgets);
    expect(find.textContaining('healthy'), findsNWidgets(2));
    expect(find.textContaining('LSD'), findsNothing);
  });
}
