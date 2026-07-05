import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/features/cattle/cattle_detail_page.dart';
import 'package:sapisehat_mobile/features/cattle/cattle_screen.dart';
import 'package:sapisehat_mobile/main.dart';

class CattleTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/farmers/farmer-1/cattle' &&
        request.method == 'POST') {
      final body = jsonDecode(request.body!);
      return ApiResponse(
        200,
        jsonEncode({
          'id': 'cattle-1',
          'farmer_id': 'farmer-1',
          'tag': body['tag'],
          'name': body['name'],
          'sex': 'female',
          'breed': 'sapi bali',
          'age_months': 24,
          'status': 'active',
          'jurisdiction_id': 'tembalang',
        }),
      );
    }
    if (request.path == '/api/farmers/farmer-1/cattle' &&
        request.method == 'GET') {
      return ApiResponse(
        200,
        jsonEncode({
          'cattle': [
            {
              'id': 'cattle-1',
              'tag': 'SAPI-001',
              'name': 'Mawar',
              'status': 'active',
            },
          ],
        }),
      );
    }
    return ApiResponse(404, '{}');
  }
}

class CattleUiTransport implements ApiTransport {
  @override
  Future<ApiResponse> send(ApiRequest request) async {
    if (request.path == '/api/farmers/farmer-1/cattle') {
      return ApiResponse(
        200,
        jsonEncode({
          'cattle': [
            {
              'id': 'cattle-1',
              'tag': 'SAPI-001',
              'name': 'Mawar',
              'status': 'active',
              'breed': 'sapi bali',
            },
          ],
        }),
      );
    }
    if (request.path == '/api/farmers/farmer-1/area-advisory') {
      return ApiResponse(
        200,
        jsonEncode({
          'farmer_id': 'farmer-1',
          'jurisdiction_id': 'tembalang',
          'advisory_active': false,
          'title': 'Tidak ada peringatan',
          'message': '',
        }),
      );
    }
    if (request.path == '/api/fusion/results') {
      return ApiResponse(200, jsonEncode({'results': []}));
    }
    return ApiResponse(404, '{}');
  }
}

final _session = AccountSession(
  token: 'token',
  farmerId: 'farmer-1',
  email: 'farmer@example.com',
);

void main() {
  test(
    'farmer can create and list cattle profiles through FastAPI contract',
    () async {
      final transport = CattleTransport();
      final api = SapiSehatApiClient(transport: transport);

      final created = await api.createCattle(
        'farmer-1',
        CattleDraft(tag: 'SAPI-001', name: 'Mawar', breed: 'sapi bali'),
      );
      final cattle = await api.listCattle('farmer-1');

      expect(created.id, 'cattle-1');
      expect(created.name, 'Mawar');
      expect(created.status, 'active');
      expect(cattle.single.tag, 'SAPI-001');
      expect(cattle.single.name, 'Mawar');
      expect(
        transport.requests.map(
          (request) => '${request.method} ${request.path}',
        ),
        [
          'POST /api/farmers/farmer-1/cattle',
          'GET /api/farmers/farmer-1/cattle',
        ],
      );
      final createBody = jsonDecode(transport.requests.first.body!);
      expect(createBody['status'], 'active');
      expect(createBody['name'], 'Mawar');
    },
  );

  testWidgets('cattle card uses cow name as title and tag below', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: CattleScreen(
            apiClient: SapiSehatApiClient(transport: CattleUiTransport()),
            session: _session,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Mawar'), findsOneWidget);
    expect(find.textContaining('SAPI-001'), findsOneWidget);
    expect(find.textContaining('SAPI-001 · Mawar'), findsNothing);
  });

  testWidgets('cattle detail app bar and header show name above tag', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: CattleDetailPage(
          apiClient: SapiSehatApiClient(transport: CattleUiTransport()),
          session: _session,
          cattle: CattleProfile(
            id: 'cattle-1',
            tag: 'SAPI-001',
            name: 'Mawar',
            status: 'active',
            breed: 'sapi bali',
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Informasi Sapi'), findsOneWidget);
    expect(find.text('Mawar'), findsOneWidget);
    expect(find.text('SAPI-001'), findsOneWidget);
  });
}
