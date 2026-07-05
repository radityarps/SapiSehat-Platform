import 'dart:convert';

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
}
