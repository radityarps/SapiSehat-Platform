import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/main.dart';

class AdvisoryTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/farmers/farmer-1/area-advisory') {
      return ApiResponse(
        200,
        jsonEncode({
          'farmer_id': 'farmer-1',
          'jurisdiction_id': 'tembalang',
          'advisory_active': true,
          'title': 'Area disease-risk advisory',
          'message':
              'Increased disease-risk reports in your district. Monitor cattle, improve biosecurity, and contact animal health officers if symptoms appear.',
          'signals': [],
          'safe_language': {
            'scope': 'district-level advisory only',
            'privacy': 'does not expose other farmers',
          },
        }),
      );
    }
    if (request.path == '/api/farmers/farmer-1/cattle') {
      return ApiResponse(200, jsonEncode({'cattle': []}));
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  test('area advisory API parses generic farmer-safe response', () async {
    final transport = AdvisoryTransport();
    final api = SapiSehatApiClient(transport: transport);
    final session = AccountSession(
      token: 'token',
      farmerId: 'farmer-1',
      email: 'farmer@example.com',
    );

    final advisory = await api.getAreaAdvisory(session);

    expect(advisory.advisoryActive, isTrue);
    expect(advisory.jurisdictionId, 'tembalang');
    expect(advisory.message.toLowerCase(), isNot(contains('diagnosis')));
    expect(advisory.message.toLowerCase(), isNot(contains('outbreak')));
    expect(
      transport.requests.single.path,
      '/api/farmers/farmer-1/area-advisory',
    );
  });

  testWidgets('cattle page shows Indonesian area advisory without identity leakage', (
    tester,
  ) async {
    final transport = AdvisoryTransport();
    final api = SapiSehatApiClient(transport: transport);
    final sessionStore = MemorySessionStore();
    final session = AccountSession(
      token: 'token',
      farmerId: 'farmer-1',
      email: 'farmer@example.com',
    );

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: HomeScreen(
            apiClient: api,
            session: session,
            sessionStore: sessionStore,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Imbauan area'), findsOneWidget);
    expect(
      find.textContaining('Ada peningkatan laporan risiko penyakit'),
      findsOneWidget,
    );
    expect(find.textContaining('Increased disease-risk reports'), findsNothing);
    expect(find.textContaining('Advisory Farmer'), findsNothing);
    expect(find.textContaining('confirmed'), findsNothing);
    expect(find.textContaining('outbreak'), findsNothing);
  });

  testWidgets('area advisory appears only on cattle page', (tester) async {
    final transport = AdvisoryTransport();
    final api = SapiSehatApiClient(transport: transport);
    final sessionStore = MemorySessionStore();
    final session = AccountSession(
      token: 'token',
      farmerId: 'farmer-1',
      email: 'farmer@example.com',
    );

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: HomeScreen(
            apiClient: api,
            session: session,
            sessionStore: sessionStore,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Imbauan area'), findsOneWidget);

    await tester.tap(find.text('Riwayat'));
    await tester.pumpAndSettle();
    expect(find.text('Imbauan area'), findsNothing);
  });
}
