import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/main.dart';

class StubTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/auth/farmer/login') {
      return ApiResponse(200, jsonEncode({
        'access_token': 'jwt-token',
        'account': {
          'id': 'farmer-1',
          'account_type': 'farmer',
          'email': 'farmer@example.com',
        },
      }));
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  testWidgets('farmer logs in against FastAPI and reaches cattle home', (tester) async {
    final transport = StubTransport();
    final sessionStore = MemorySessionStore();

    await tester.pumpWidget(SapiSehatApp(
      apiClient: SapiSehatApiClient(transport: transport),
      sessionStore: sessionStore,
    ));

    await tester.tap(find.text('Lewati'));
    await tester.pumpAndSettle();

    await tester.enterText(find.bySemanticsLabel('Email'), 'farmer@example.com');
    await tester.enterText(find.bySemanticsLabel('Password'), 'strong-password');
    await tester.tap(find.text('Masuk').last);
    await tester.pumpAndSettle();

    expect(find.text('Kandang Sapi'), findsOneWidget);
    expect(find.text('Sinyal risiko, bukan diagnosis'), findsOneWidget);
    expect(sessionStore.token, 'jwt-token');
    final loginRequest = transport.requests.firstWhere((request) => request.path == '/api/auth/farmer/login');
    expect(transport.requests.where((request) => request.path == '/api/auth/farmer/login').length, 1);
    expect(jsonDecode(loginRequest.body!)['email'], 'farmer@example.com');
  });
}
