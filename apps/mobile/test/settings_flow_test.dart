import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/features/settings/settings_screen.dart';
import 'package:sapisehat_mobile/main.dart';

class SettingsTransport implements ApiTransport {
  ApiRequest? lastProfileUpdate;
  ApiRequest? lastArchive;

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    if (request.method == 'PUT' &&
        request.path == '/api/farmers/farmer-1/profile') {
      lastProfileUpdate = request;
      return ApiResponse(
        200,
        jsonEncode({
          'id': 'farmer-1',
          'account_type': 'farmer',
          'email': 'farmer@example.com',
          'is_active': true,
          'name': 'Demo Farmer',
          'jurisdiction_id': 'tembalang',
          'address': 'Jl. Sapi Sehat 1',
        }),
      );
    }
    if (request.method == 'POST' &&
        request.path == '/api/farmers/farmer-1/account/archive') {
      lastArchive = request;
      return ApiResponse(
        200,
        jsonEncode({
          'id': 'farmer-1',
          'account_type': 'farmer',
          'email': 'farmer@example.com',
          'is_active': false,
        }),
      );
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  test('profile update sends and reads address', () async {
    final transport = SettingsTransport();
    final updated = await SapiSehatApiClient(transport: transport)
        .updateFarmerProfile(
          AccountSession(
            token: 'token',
            farmerId: 'farmer-1',
            email: 'farmer@example.com',
          ),
          FarmerProfileDraft(
            name: 'Demo Farmer',
            jurisdictionId: 'tembalang',
            address: 'Jl. Sapi Sehat 1',
          ),
        );

    expect(transport.lastProfileUpdate?.path, '/api/farmers/farmer-1/profile');
    expect(
      jsonDecode(transport.lastProfileUpdate!.body!)['address'],
      'Jl. Sapi Sehat 1',
    );
    expect(updated.address, 'Jl. Sapi Sehat 1');
  });

  test('delete account uses archive endpoint', () async {
    final transport = SettingsTransport();
    final archived = await SapiSehatApiClient(transport: transport)
        .deleteFarmerAccount(
          AccountSession(
            token: 'token',
            farmerId: 'farmer-1',
            email: 'farmer@example.com',
          ),
          'strong-password',
        );

    expect(
      transport.lastArchive?.path,
      '/api/farmers/farmer-1/account/archive',
    );
    expect(
      jsonDecode(transport.lastArchive!.body!)['password'],
      'strong-password',
    );
    expect(archived.isActive, isFalse);
  });

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

  testWidgets('delete account password field has visibility toggle', (
    tester,
  ) async {
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
            onLogout: () async {},
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.text('Hapus akun'), 500);

    await tester.tap(find.text('Hapus akun'));
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.visibility), findsOneWidget);
    expect(
      tester.widget<TextField>(find.byType(TextField)).obscureText,
      isTrue,
    );

    await tester.tap(find.byIcon(Icons.visibility));
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.visibility_off), findsOneWidget);
    expect(
      tester.widget<TextField>(find.byType(TextField)).obscureText,
      isFalse,
    );
  });
}
