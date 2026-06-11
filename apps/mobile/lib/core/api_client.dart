import 'dart:convert';

import '../features/auth/auth.dart';
import '../features/cattle/cattle.dart';
import '../features/history/history.dart';
import '../features/scan/scan.dart';
import '../features/settings/settings.dart';
import 'api.dart';

class SapiSehatApiClient {
  SapiSehatApiClient({ApiTransport? transport}) : transport = transport ?? HttpApiTransport();
  final ApiTransport transport;

  Map<String, String> _auth(AccountSession session) => {'Accept': 'application/json', 'Authorization': 'Bearer ${session.token}'};

  AccountSession _sessionFromJson(Map<String, dynamic> body) {
    final account = body['account'] as Map<String, dynamic>;
    return AccountSession(
      token: body['access_token'] as String? ?? '',
      farmerId: account['id'] as String,
      email: account['email'] as String,
      name: account['name'] as String? ?? '',
      jurisdictionId: account['jurisdiction_id'] as String? ?? 'tembalang',
      isActive: account['is_active'] as bool? ?? true,
    );
  }

  Future<AccountSession> loginFarmer(String email, String password) async {
    final response = await transport.send(ApiRequest('POST', '/api/auth/farmer/login', body: jsonEncode({'email': email, 'password': password}), headers: {'Accept': 'application/json'}));
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception('Login failed');
    return _sessionFromJson(response.json);
  }

  Future<AccountSession> registerFarmer(FarmerRegistrationDraft draft) async {
    final response = await transport.send(ApiRequest('POST', '/api/auth/farmer/register', body: jsonEncode(draft.toJson()), headers: {'Accept': 'application/json'}));
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception('Register failed');
    return _sessionFromJson(response.json);
  }

  Future<AccountSession> updateFarmerProfile(AccountSession session, FarmerProfileDraft draft) async {
    final response = await transport.send(ApiRequest('PUT', '/api/farmers/${session.farmerId}/profile', body: jsonEncode(draft.toJson()), headers: _auth(session)));
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception('Profile update failed');
    final account = response.json;
    return session.copyWith(name: account['name'] as String? ?? draft.name, jurisdictionId: account['jurisdiction_id'] as String? ?? draft.jurisdictionId, isActive: account['is_active'] as bool? ?? true);
  }

  Future<AccountSession> archiveFarmerAccount(AccountSession session, String password) async {
    final response = await transport.send(ApiRequest('POST', '/api/farmers/${session.farmerId}/account/archive', body: jsonEncode({'password': password}), headers: _auth(session)));
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception('Archive failed');
    return session.copyWith(isActive: false);
  }

  Future<FarmerPreferences> getPreferences(AccountSession session) async {
    final response = await transport.send(ApiRequest('GET', '/api/farmers/${session.farmerId}/preferences', headers: _auth(session)));
    if (response.statusCode != 200) throw Exception('Preferences failed');
    return FarmerPreferences.fromJson(response.json);
  }

  Future<FarmerPreferences> updatePreferences(AccountSession session, FarmerPreferences preferences) async {
    final response = await transport.send(ApiRequest('PUT', '/api/farmers/${session.farmerId}/preferences', body: jsonEncode(preferences.toJson()), headers: _auth(session)));
    if (response.statusCode != 200) throw Exception('Preferences update failed');
    return FarmerPreferences.fromJson(response.json);
  }

  Future<List<CattleProfile>> listCattle(String farmerId) async {
    final response = await transport.send(ApiRequest('GET', '/api/farmers/$farmerId/cattle'));
    if (response.statusCode != 200) throw Exception('Cattle list failed');
    final cattle = response.json['cattle'] as List<dynamic>;
    return cattle.map((item) => CattleProfile.fromJson(item as Map<String, dynamic>)).where((item) => !item.isArchived).toList();
  }

  Future<CattleProfile> createCattle(String farmerId, CattleDraft draft) async {
    final response = await transport.send(ApiRequest('POST', '/api/farmers/$farmerId/cattle', body: jsonEncode(draft.toJson()), headers: {'Accept': 'application/json'}));
    if (response.statusCode != 200) throw Exception('Create cattle failed');
    return CattleProfile.fromJson(response.json);
  }

  Future<CattleProfile> updateCattle(String farmerId, CattleProfile cattle) async {
    final response = await transport.send(ApiRequest('PUT', '/api/farmers/$farmerId/cattle/${cattle.id}', body: jsonEncode({'tag': cattle.tag, 'status': cattle.status, 'sex': cattle.sex, 'breed': cattle.breed, 'age_months': cattle.ageMonths, 'jurisdiction_id': cattle.jurisdictionId, 'is_archived': cattle.isArchived}), headers: {'Accept': 'application/json'}));
    if (response.statusCode != 200) throw Exception('Update cattle failed');
    return CattleProfile.fromJson(response.json);
  }

  Future<CattleProfile> archiveCattle(String farmerId, String cattleId) async {
    final response = await transport.send(ApiRequest('POST', '/api/farmers/$farmerId/cattle/$cattleId/archive', headers: {'Accept': 'application/json'}));
    if (response.statusCode != 200) throw Exception('Archive cattle failed');
    return CattleProfile.fromJson(response.json);
  }

  Future<ScanResult> uploadScan({required String farmerId, String? cattleId, required List<int> bytes}) async {
    final prediction = await transport.send(ApiRequest('POST', '/api/predict', body: 'multipart:file:${bytes.length}'));
    if (prediction.statusCode < 200 || prediction.statusCode >= 300) throw Exception('Prediction failed');
    final diseaseClass = ((prediction.json['prediction'] as Map?)?['disease_class'] ?? 'needs_review') as String;
    final confidence = (((prediction.json['prediction'] as Map?)?['confidence'] ?? 0.0) as num).toDouble();
    final media = await transport.send(ApiRequest('POST', '/api/media/uploads', body: 'multipart:file:${bytes.length}'));
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
