import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/main.dart';

class StubTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/auth/farmer/login') {
      return ApiResponse(
        200,
        jsonEncode({
          'access_token': 'jwt-token',
          'account': {
            'id': 'farmer-1',
            'account_type': 'farmer',
            'email': 'farmer@example.com',
          },
        }),
      );
    }
    if (request.path == '/api/auth/farmer/register') {
      return ApiResponse(
        200,
        jsonEncode({
          'access_token': 'register-token',
          'account': {
            'id': 'farmer-1',
            'account_type': 'farmer',
            'email': 'new@example.com',
            'name': 'Pak Baru',
            'jurisdiction_id': 'tembalang',
            'address': 'Jl. Sapi Sehat 1',
          },
        }),
      );
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  test('farmer register sends and reads address', () async {
    final transport = StubTransport();
    final session = await SapiSehatApiClient(transport: transport)
        .registerFarmer(
          FarmerRegistrationDraft(
            name: 'Pak Baru',
            email: 'new@example.com',
            password: 'strong-password',
            jurisdictionId: 'tembalang',
            address: 'Jl. Sapi Sehat 1',
          ),
        );

    final request = transport.requests.singleWhere(
      (request) => request.path == '/api/auth/farmer/register',
    );
    expect(jsonDecode(request.body!)['address'], 'Jl. Sapi Sehat 1');
    expect(session.address, 'Jl. Sapi Sehat 1');
  });

  testWidgets('farmer logs in against FastAPI and reaches cattle home', (
    tester,
  ) async {
    final transport = StubTransport();
    final sessionStore = MemorySessionStore();

    await tester.pumpWidget(
      SapiSehatApp(
        apiClient: SapiSehatApiClient(transport: transport),
        sessionStore: sessionStore,
      ),
    );

    await tester.tap(find.text('Lewati'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.bySemanticsLabel('Email'),
      'farmer@example.com',
    );
    await tester.enterText(
      find.bySemanticsLabel('Password'),
      'strong-password',
    );
    await tester.tap(find.text('Masuk').last);
    await tester.pumpAndSettle();

    expect(find.text('Kandang Sapi'), findsOneWidget);
    expect(find.text('Sinyal risiko, bukan diagnosis'), findsNothing);
    expect(sessionStore.token, 'jwt-token');
    final loginRequest = transport.requests.firstWhere(
      (request) => request.path == '/api/auth/farmer/login',
    );
    expect(
      transport.requests
          .where((request) => request.path == '/api/auth/farmer/login')
          .length,
      1,
    );
    expect(jsonDecode(loginRequest.body!)['email'], 'farmer@example.com');
  });

  test('FileSessionStore persists session and expires after 7 days', () async {
    final tempDir = await Directory.systemTemp.createTemp('sapisehat_auth_test_');
    try {
      final store = FileSessionStore(directoryProvider: () async => tempDir);
      final session = AccountSession(
        token: 'test-token',
        farmerId: 'farmer-test',
        email: 'test@example.com',
        name: 'Test Farmer',
      );

      expect(await store.load(), isNull);
      await store.save(session);

      final loaded = await store.load();
      expect(loaded, isNotNull);
      expect(loaded!.token, 'test-token');
      expect(loaded.farmerId, 'farmer-test');
      expect(loaded.email, 'test@example.com');

      // Test expiration with negative TTL
      final expiredStore = FileSessionStore(
        directoryProvider: () async => tempDir,
        ttl: const Duration(milliseconds: -1),
      );
      expect(await expiredStore.load(), isNull);
    } finally {
      await tempDir.delete(recursive: true);
    }
  });

  testWidgets('already authenticated user automatically redirects to home screen', (
    tester,
  ) async {
    final session = AccountSession(
      token: 'persisted-token',
      farmerId: 'farmer-1',
      email: 'farmer@example.com',
      name: 'Peternak Setia',
    );
    final sessionStore = MemorySessionStore(initialSession: session);

    await tester.pumpWidget(
      SapiSehatApp(
        apiClient: SapiSehatApiClient(transport: StubTransport()),
        sessionStore: sessionStore,
        initialSession: session,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Kandang Sapi'), findsOneWidget);
    expect(find.text('Sinyal risiko, bukan diagnosis'), findsNothing);
    expect(find.text('Lewati'), findsNothing);
  });
}
