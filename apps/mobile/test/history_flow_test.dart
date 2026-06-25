import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/main.dart';

class HistoryTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/fusion/results') {
      return ApiResponse(200, jsonEncode({
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
          }
        ]
      }));
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  test('detection history returns farmer-scoped risk signals without diagnosis copy', () async {
    final transport = HistoryTransport();
    final api = SapiSehatApiClient(transport: transport);

    final history = await api.listDetectionHistory('farmer-1');

    expect(history.single.id, 'fusion-1');
    expect(history.single.label, 'FMD');
    expect(history.single.safeSummary, 'Risk signal: FMD');
    expect(history.single.safeSummary.toLowerCase(), isNot(contains('diagnosis')));
    expect(transport.requests.single.path, '/api/fusion/results');
  });
}
