import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/main.dart';

void main() {
  testWidgets('app boots to onboarding shell', (tester) async {
    await tester.pumpWidget(SapiSehatApp(
      apiClient: SapiSehatApiClient(transport: _NoopTransport()),
      sessionStore: MemorySessionStore(),
    ));

    expect(find.text('SapiSehat'), findsOneWidget);
    expect(find.text('Lewati'), findsOneWidget);
    expect(find.text('Kelola kesehatan sapi'), findsOneWidget);
  });
}

class _NoopTransport implements ApiTransport {
  @override
  Future<ApiResponse> send(ApiRequest request) async => ApiResponse(404, '{}');
}
