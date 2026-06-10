import 'dart:convert';

import '../features/auth/auth.dart';
import '../features/cattle/cattle.dart';
import '../features/history/history.dart';
import '../features/scan/scan.dart';
import 'api.dart';

class SapiSehatApiClient {
  SapiSehatApiClient({ApiTransport? transport}) : transport = transport ?? HttpApiTransport();
  final ApiTransport transport;

  Future<AccountSession> loginFarmer(String email, String password) async {
    final response = await transport.send(ApiRequest(
      'POST',
      '/api/auth/farmer/login',
      body: jsonEncode({'email': email, 'password': password}),
      headers: {'Accept': 'application/json'},
    ));
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception('Login failed');
    final body = response.json;
    final account = body['account'] as Map<String, dynamic>;
    return AccountSession(token: body['access_token'] as String, farmerId: account['id'] as String, email: account['email'] as String);
  }

  Future<List<CattleProfile>> listCattle(String farmerId) async {
    final response = await transport.send(ApiRequest('GET', '/api/farmers/$farmerId/cattle'));
    if (response.statusCode != 200) throw Exception('Cattle list failed');
    final cattle = response.json['cattle'] as List<dynamic>;
    return cattle.map((item) => CattleProfile.fromJson(item as Map<String, dynamic>)).toList();
  }

  Future<CattleProfile> createCattle(String farmerId, CattleDraft draft) async {
    final response = await transport.send(ApiRequest('POST', '/api/farmers/$farmerId/cattle', body: jsonEncode(draft.toJson()), headers: {'Accept': 'application/json'}));
    if (response.statusCode != 200) throw Exception('Create cattle failed');
    return CattleProfile.fromJson(response.json);
  }

  Future<ScanResult> uploadScan({required String farmerId, String? cattleId, required List<int> bytes}) async {
    final prediction = await transport.send(ApiRequest('POST', '/api/predict', body: 'image-bytes'));
    if (prediction.statusCode < 200 || prediction.statusCode >= 300) throw Exception('Prediction failed');
    final diseaseClass = ((prediction.json['prediction'] as Map?)?['disease_class'] ?? 'needs_review') as String;
    final confidence = (((prediction.json['prediction'] as Map?)?['confidence'] ?? 0.0) as num).toDouble();
    final media = await transport.send(ApiRequest('POST', '/api/media/uploads', body: 'multipart-image'));
    if (media.statusCode < 200 || media.statusCode >= 300) throw Exception('Media upload failed');
    return ScanResult(localId: 'online-${DateTime.now().microsecondsSinceEpoch}', cattleId: cattleId, label: diseaseClass, confidence: confidence, capturedAt: DateTime.now(), inferenceMode: 'online', syncStatus: 'synced');
  }

  Future<void> syncOffline(PendingOfflineDetection detection) async {
    final response = await transport.send(ApiRequest('POST', '/api/offline/detections/sync', body: jsonEncode(detection.toSyncJson())));
    if (response.statusCode != 200) throw Exception('Offline sync failed');
  }

  Future<List<DetectionHistoryItem>> listDetectionHistory(String farmerId) async {
    final response = await transport.send(ApiRequest('GET', '/api/fusion/results'));
    if (response.statusCode != 200) throw Exception('Detection history failed');
    final results = response.json['results'] as List<dynamic>;
    return results.map((item) => DetectionHistoryItem.fromJson(item as Map<String, dynamic>)).where((item) => item.farmerId == farmerId).toList();
  }
}
