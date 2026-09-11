import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

import 'app/sapi_sehat_app.dart';
import 'core/api.dart';
import 'features/auth/auth.dart';

export 'app/sapi_sehat_app.dart';
export 'core/api.dart';
export 'core/api_client.dart';
export 'features/advisory/advisory.dart';
export 'features/auth/auth.dart';
export 'features/cattle/cattle.dart';
export 'features/history/history.dart';
export 'features/guide/guide_catalog.dart';
export 'features/guide/guide_screen.dart';
export 'features/scan/scan.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: '.env', isOptional: true);
  ApiConfig.baseUrl =
      dotenv.env['SAPISEHAT_API_BASE_URL'] ?? ApiConfig.defaultBaseUrl;
  final sessionStore = FileSessionStore();
  final initialSession = await sessionStore.load();
  runApp(SapiSehatApp(
    sessionStore: sessionStore,
    initialSession: initialSession,
  ));
}
