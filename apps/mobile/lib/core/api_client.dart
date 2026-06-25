import 'dart:convert';

import '../features/auth/auth.dart';
import '../features/cattle/cattle.dart';
import '../features/history/history.dart';
import '../features/scan/scan.dart';
import '../features/settings/settings.dart';
import 'api.dart';

class FarmerAreaAdvisory {
  const FarmerAreaAdvisory({
    required this.farmerId,
    required this.jurisdictionId,
    required this.advisoryActive,
    required this.title,
    required this.message,
  });

  final String farmerId;
  final String jurisdictionId;
  final bool advisoryActive;
  final String title;
  final String message;

  factory FarmerAreaAdvisory.fromJson(Map<String, dynamic> json) =>
      FarmerAreaAdvisory(
        farmerId: json['farmer_id'] as String? ?? '',
        jurisdictionId: json['jurisdiction_id'] as String? ?? '',
        advisoryActive: json['advisory_active'] as bool? ?? false,
        title: json['title'] as String? ?? 'Area advisory',
        message: json['message'] as String? ?? '',
      );
}

class SapiSehatApiClient {
  SapiSehatApiClient({ApiTransport? transport})
    : transport = transport ?? HttpApiTransport();
  final ApiTransport transport;

  Map<String, String> _auth(AccountSession session) => {
    'Accept': 'application/json',
    'Authorization': 'Bearer ${session.token}',
  };

  AccountSession _sessionFromJson(Map<String, dynamic> body) {
    final account = body['account'] as Map<String, dynamic>;
    return AccountSession(
      token: body['access_token'] as String? ?? '',
      farmerId: account['id'] as String,
      email: account['email'] as String,
      name: account['name'] as String? ?? '',
      address: account['address'] as String?,
      jurisdictionId: account['jurisdiction_id'] as String? ?? 'tembalang',
      isActive: account['is_active'] as bool? ?? true,
    );
  }

  Future<AccountSession> loginFarmer(String email, String password) async {
    final response = await transport.send(
      ApiRequest(
        'POST',
        '/api/auth/farmer/login',
        body: jsonEncode({'email': email, 'password': password}),
        headers: {'Accept': 'application/json'},
      ),
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Login failed');
    }
    return _sessionFromJson(response.json);
  }

  Future<AccountSession> registerFarmer(FarmerRegistrationDraft draft) async {
    final response = await transport.send(
      ApiRequest(
        'POST',
        '/api/auth/farmer/register',
        body: jsonEncode(draft.toJson()),
        headers: {'Accept': 'application/json'},
      ),
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Register failed');
    }
    return _sessionFromJson(response.json);
  }

  Future<AccountSession> updateFarmerProfile(
    AccountSession session,
    FarmerProfileDraft draft,
  ) async {
    final response = await transport.send(
      ApiRequest(
        'PUT',
        '/api/farmers/${session.farmerId}/profile',
        body: jsonEncode(draft.toJson()),
        headers: _auth(session),
      ),
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Profile update failed');
    }
    final account = response.json;
    return session.copyWith(
      name: account['name'] as String? ?? draft.name,
      address: account['address'] as String? ?? draft.address,
      jurisdictionId:
          account['jurisdiction_id'] as String? ?? draft.jurisdictionId,
      isActive: account['is_active'] as bool? ?? true,
    );
  }

  Future<AccountSession> deleteFarmerAccount(
    AccountSession session,
    String password,
  ) async {
    final response = await transport.send(
      ApiRequest(
        'POST',
        '/api/farmers/${session.farmerId}/account/delete',
        body: jsonEncode({'password': password}),
        headers: _auth(session),
      ),
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Delete account failed');
    }
    return session.copyWith(isActive: false);
  }

  Future<void> changePassword(
    AccountSession session, {
    required String currentPassword,
    required String newPassword,
  }) async {
    final response = await transport.send(
      ApiRequest(
        'POST',
        '/api/farmers/${session.farmerId}/account/change-password',
        body: jsonEncode({
          'current_password': currentPassword,
          'new_password': newPassword,
        }),
        headers: _auth(session),
      ),
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Change password failed');
    }
  }

  Future<FarmerPreferences> getPreferences(AccountSession session) async {
    final response = await transport.send(
      ApiRequest(
        'GET',
        '/api/farmers/${session.farmerId}/preferences',
        headers: _auth(session),
      ),
    );
    if (response.statusCode != 200) throw Exception('Preferences failed');
    return FarmerPreferences.fromJson(response.json);
  }

  Future<FarmerPreferences> updatePreferences(
    AccountSession session,
    FarmerPreferences preferences,
  ) async {
    final response = await transport.send(
      ApiRequest(
        'PUT',
        '/api/farmers/${session.farmerId}/preferences',
        body: jsonEncode(preferences.toJson()),
        headers: _auth(session),
      ),
    );
    if (response.statusCode != 200) {
      throw Exception('Preferences update failed');
    }
    return FarmerPreferences.fromJson(response.json);
  }

  Future<FarmerAreaAdvisory> getAreaAdvisory(AccountSession session) async {
    final response = await transport.send(
      ApiRequest(
        'GET',
        '/api/farmers/${session.farmerId}/area-advisory',
        headers: _auth(session),
      ),
    );
    if (response.statusCode != 200) {
      throw Exception('Area advisory failed');
    }
    return FarmerAreaAdvisory.fromJson(response.json);
  }

  Future<List<CattleProfile>> listCattle(String farmerId) async {
    final response = await transport.send(
      ApiRequest('GET', '/api/farmers/$farmerId/cattle'),
    );
    if (response.statusCode != 200) throw Exception('Cattle list failed');
    final cattle = response.json['cattle'] as List<dynamic>;
    return cattle
        .map((item) => CattleProfile.fromJson(item as Map<String, dynamic>))
        .where((item) => !item.isArchived)
        .toList();
  }

  Future<CattleProfile> createCattle(String farmerId, CattleDraft draft) async {
    final response = await transport.send(
      ApiRequest(
        'POST',
        '/api/farmers/$farmerId/cattle',
        body: jsonEncode(draft.toJson()),
        headers: {'Accept': 'application/json'},
      ),
    );
    if (response.statusCode != 200) throw Exception('Create cattle failed');
    return CattleProfile.fromJson(response.json);
  }

  Future<CattleProfile> updateCattle(
    String farmerId,
    CattleProfile cattle,
  ) async {
    final response = await transport.send(
      ApiRequest(
        'PUT',
        '/api/farmers/$farmerId/cattle/${cattle.id}',
        body: jsonEncode({
          'tag': cattle.tag,
          'status': cattle.status,
          'sex': cattle.sex,
          'breed': cattle.breed,
          'age_months': cattle.ageMonths,
          'birth_year_estimate': cattle.birthYearEstimate,
          'jurisdiction_id': cattle.jurisdictionId,
          'is_archived': cattle.isArchived,
          'name': cattle.name,
          'color': cattle.color,
          'weight_kg': cattle.weightKg,
          'reproductive_status': cattle.reproductiveStatus,
          'is_pregnant': cattle.isPregnant,
          'last_calving_date': cattle.lastCalvingDate,
          'last_vaccination_date': cattle.lastVaccinationDate,
          'last_deworming_date': cattle.lastDewormingDate,
          'health_notes': cattle.healthNotes,
          'purchase_date': cattle.purchaseDate,
          'purchase_price_idr': cattle.purchasePriceIdr,
          'notes': cattle.notes,
        }),
        headers: {'Accept': 'application/json'},
      ),
    );
    if (response.statusCode != 200) throw Exception('Update cattle failed');
    return CattleProfile.fromJson(response.json);
  }

  Future<CattleProfile> archiveCattle(String farmerId, String cattleId) async {
    final response = await transport.send(
      ApiRequest(
        'DELETE',
        '/api/farmers/$farmerId/cattle/$cattleId',
        headers: {'Accept': 'application/json'},
      ),
    );
    if (response.statusCode != 200) throw Exception('Archive cattle failed');
    return CattleProfile.fromJson(response.json);
  }

  Future<ScanResult> uploadScan({
    required String farmerId,
    String? cattleId,
    required List<int> bytes,
  }) async {
    final scan = await predictScan(bytes: bytes);
    return saveScanResult(farmerId: farmerId, cattleId: cattleId, result: scan);
  }

  Future<ScanResult> predictScan({required List<int> bytes}) async {
    final prediction = await transport.send(
      ApiRequest(
        'POST',
        '/api/predict',
        fileField: 'image',
        fileName: 'scan.jpg',
        fileBytes: bytes,
        fileContentType: 'image/jpeg',
      ),
    );
    if (prediction.statusCode < 200 || prediction.statusCode >= 300) {
      throw Exception('Prediction failed');
    }
    final diseaseClass =
        ((prediction.json['prediction'] as Map?)?['disease_class'] ??
                'needs_review')
            as String;
    final confidence =
        (((prediction.json['prediction'] as Map?)?['confidence'] ?? 0.0) as num)
            .toDouble();
    return ScanResult(
      localId: 'online-${DateTime.now().microsecondsSinceEpoch}',
      label: diseaseClass,
      confidence: confidence,
      capturedAt: DateTime.now(),
      inferenceMode: 'online',
      syncStatus: 'unsaved',
    );
  }

  Future<ScanResult> saveScanResult({
    required String farmerId,
    String? cattleId,
    required ScanResult result,
  }) async {
    final fusion = await transport.send(
      ApiRequest(
        'POST',
        '/api/fusion/results',
        body: jsonEncode({
          'farmer_id': farmerId,
          'cattle_id': cattleId,
          'image_evidence': {
            'source': 'image',
            'model_version': 'mobile-online',
            'inference_mode': 'online',
            'disease_scores': {
              'healthy': result.label == 'healthy' ? result.confidence : 0.0,
              'FMD': result.label == 'FMD' ? result.confidence : 0.0,
              'LSD': result.label == 'LSD' ? result.confidence : 0.0,
            },
            'top_class': result.label,
            'confidence': result.confidence,
            'quality_status': 'accepted',
            'rejection_reasons': [],
          },
          'nlp_evidence': null,
        }),
        headers: {'Accept': 'application/json'},
      ),
    );
    if (fusion.statusCode < 200 || fusion.statusCode >= 300) {
      throw Exception('Fusion result failed');
    }
    final fusedClass = (fusion.json['disease_class'] ?? result.label) as String;
    final fusedConfidence =
        ((fusion.json['confidence'] ?? result.confidence) as num).toDouble();
    return ScanResult(
      localId: result.localId,
      cattleId: cattleId,
      label: fusedClass,
      confidence: fusedConfidence,
      capturedAt: result.capturedAt,
      inferenceMode: result.inferenceMode,
      syncStatus: 'synced',
      imagePath: result.imagePath,
    );
  }

  Future<void> syncOffline(PendingOfflineDetection detection) async {
    final response = await transport.send(
      ApiRequest(
        'POST',
        '/api/offline/detections/sync',
        body: jsonEncode(detection.toSyncJson()),
      ),
    );
    if (response.statusCode != 200) throw Exception('Offline sync failed');
  }

  Future<List<DetectionHistoryItem>> listDetectionHistory(
    String farmerId,
  ) async {
    final response = await transport.send(
      ApiRequest('GET', '/api/fusion/results'),
    );
    if (response.statusCode != 200) throw Exception('Detection history failed');
    final results = response.json['results'] as List<dynamic>;
    return results
        .map(
          (item) => DetectionHistoryItem.fromJson(item as Map<String, dynamic>),
        )
        .where((item) => item.farmerId == farmerId)
        .toList();
  }
}
