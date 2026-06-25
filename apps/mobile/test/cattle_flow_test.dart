import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/main.dart';

class CattleTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/farmers/farmer-1/cattle' && request.method == 'POST') {
      return ApiResponse(200, jsonEncode({
        'id': 'cattle-1',
        'farmer_id': 'farmer-1',
        'tag': jsonDecode(request.body!)['tag'],
        'sex': 'female',
        'breed': 'sapi bali',
        'age_months': 24,
        'status': 'active',
        'jurisdiction_id': 'tembalang',
      }));
    }
    if (request.path == '/api/farmers/farmer-1/cattle' && request.method == 'GET') {
      return ApiResponse(200, jsonEncode({
        'cattle': [
          {'id': 'cattle-1', 'tag': 'SAPI-001', 'status': 'active'}
        ]
      }));
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  test('farmer can create and list cattle profiles through FastAPI contract', () async {
    final transport = CattleTransport();
    final api = SapiSehatApiClient(transport: transport);

    final created = await api.createCattle('farmer-1', CattleDraft(tag: 'SAPI-001', breed: 'sapi bali'));
    final cattle = await api.listCattle('farmer-1');

    expect(created.id, 'cattle-1');
    expect(created.status, 'active');
    expect(cattle.single.tag, 'SAPI-001');
    expect(transport.requests.map((request) => '${request.method} ${request.path}'), [
      'POST /api/farmers/farmer-1/cattle',
      'GET /api/farmers/farmer-1/cattle',
    ]);
    expect(jsonDecode(transport.requests.first.body!)['status'], 'active');
  });
}
