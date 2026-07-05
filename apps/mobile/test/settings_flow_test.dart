import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/features/settings/settings_screen.dart';
import 'package:sapisehat_mobile/main.dart';

class SettingsTransport implements ApiTransport {
  @override
  Future<ApiResponse> send(ApiRequest request) async {
    if (request.path == '/api/farmers/farmer-1/preferences') {
      return ApiResponse(
        200,
        jsonEncode({
          'farmer_id': 'farmer-1',
          'scan_result_notifications': true,
          'sync_notifications': true,
          'area_risk_advisory_notifications': false,
          'follow_up_status_notifications': true,
        }),
      );
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  testWidgets('logout confirms and shows success toast', (tester) async {
    var loggedOut = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SettingsScreen(
            apiClient: SapiSehatApiClient(transport: SettingsTransport()),
            session: AccountSession(
              token: 'token',
              farmerId: 'farmer-1',
              email: 'farmer@example.com',
            ),
            sessionStore: MemorySessionStore(),
            onSessionChanged: (_) {},
            onArchived: () {},
            onLogout: () async {
              loggedOut = true;
            },
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.text('Keluar'), 500);

    await tester.tap(find.text('Keluar'));
    await tester.pumpAndSettle();
    expect(find.text('Keluar dari akun?'), findsOneWidget);

    await tester.tap(find.text('Batal'));
    await tester.pumpAndSettle();
    expect(loggedOut, isFalse);

    await tester.tap(find.text('Keluar'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Keluar').last);
    await tester.pumpAndSettle();

    expect(loggedOut, isTrue);
    expect(find.text('Berhasil keluar.'), findsOneWidget);
  });

  testWidgets('logout shows failure toast', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SettingsScreen(
            apiClient: SapiSehatApiClient(transport: SettingsTransport()),
            session: AccountSession(
              token: 'token',
              farmerId: 'farmer-1',
              email: 'farmer@example.com',
            ),
            sessionStore: MemorySessionStore(),
            onSessionChanged: (_) {},
            onArchived: () {},
            onLogout: () async => throw Exception('logout failed'),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.text('Keluar'), 500);

    await tester.tap(find.text('Keluar'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Keluar').last);
    await tester.pumpAndSettle();

    expect(find.text('Gagal keluar. Coba lagi.'), findsOneWidget);
  });
}
