import 'dart:convert';
import 'dart:io' show IOException;

import '../features/auth/auth.dart';
import '../features/cattle/cattle.dart';
import '../features/history/history.dart';
import '../features/scan/offline_inference.dart';
import '../features/scan/scan.dart';
import 'api.dart';

class ApiRequestException implements Exception {
  const ApiRequestException(this.statusCode, this.message, {this.errorCode});
  final int statusCode;
  final String message;
  final String? errorCode;

  bool get isAvailabilityFailure => statusCode >= 500 || statusCode == 408;

  @override
  String toString() => message;
}

class InvalidPredictionException implements Exception {
  const InvalidPredictionException(this.message);
  final String message;

  @override
  String toString() => message;
}

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
  SapiSehatApiClient({
    ApiTransport? transport,
    OfflineInferenceService? offlineInferenceService,
  }) : transport = transport ?? HttpApiTransport(),
       offlineInferenceService =
           offlineInferenceService ?? OfflineInferenceService();

  final ApiTransport transport;
  final OfflineInferenceService offlineInferenceService;

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
      clearAddress: (account['address'] as String? ?? draft.address) == null,
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
        '/api/farmers/${session.farmerId}/account/archive',
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
    ApiRequestException? availabilityError;
    try {
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
      if (prediction.statusCode >= 200 && prediction.statusCode < 300) {
        return _onlineScanResult(prediction.json);
      }
      final error = _apiError(prediction);
      if (!error.isAvailabilityFailure) throw error;
      availabilityError = error;
    } on ApiRequestException catch (error) {
      if (!error.isAvailabilityFailure) rethrow;
      availabilityError = error;
    } on IOException {
      // Transport availability failures use the offline model.
    } on NonCattleImageException {
      rethrow;
    }

    OfflineInferenceResult offline;
    try {
      offline = await offlineInferenceService.infer(bytes);
    } on FormatException catch (_) {
      final message = availabilityError?.errorCode == 'MODEL_NOT_READY'
          ? 'Model deteksi belum siap digunakan. Coba lagi setelah model diverifikasi.'
          : 'Layanan online tidak tersedia dan model offline belum siap digunakan.';
      throw DetectionUnavailableException(message);
    }
    return ScanResult(
      localId: 'offline-${DateTime.now().microsecondsSinceEpoch}',
      label: offline.label,
      confidence: offline.confidence,
      capturedAt: DateTime.now(),
      inferenceMode: 'offline',
      syncStatus: 'unsaved',
      modelVersion: offline.modelVersion,
      scores: offline.scores,
    );
  }

  ScanResult _onlineScanResult(Map<String, dynamic> body) {
    final prediction = body['prediction'];
    final modelInfo = body['model_info'];
    if (prediction is! Map || modelInfo is! Map) {
      throw const InvalidPredictionException('Invalid prediction response');
    }
    final label = prediction['disease_class'];
    final confidence = prediction['confidence'];
    final rawScores = prediction['scores'];
    final version = modelInfo['version'];
    if (label is! String ||
        !activeDetectionClasses.contains(label) ||
        confidence is! num ||
        version is! String ||
        version.isEmpty ||
        rawScores is! Map ||
        rawScores.length != activeDetectionClasses.length ||
        rawScores.keys.toSet().containsAll(activeDetectionClasses) == false) {
      throw const InvalidPredictionException(
        'Invalid active prediction response',
      );
    }
    final scores = <String, double>{};
    for (final key in activeDetectionClasses) {
      final value = rawScores[key];
      if (value is! num || !value.isFinite || value < 0 || value > 1) {
        throw const InvalidPredictionException(
          'Invalid active prediction scores',
        );
      }
      scores[key] = value.toDouble();
    }
    if (!confidence.isFinite ||
        confidence < 0 ||
        confidence > 1 ||
        (scores[label]! - confidence.toDouble()).abs() >= 0.001) {
      throw const InvalidPredictionException('Invalid prediction confidence');
    }
    return ScanResult(
      localId: 'online-${DateTime.now().microsecondsSinceEpoch}',
      label: label,
      confidence: confidence.toDouble(),
      capturedAt: DateTime.now(),
      inferenceMode: 'online',
      syncStatus: 'unsaved',
      modelVersion: version,
      scores: scores,
    );
  }

  ApiRequestException _apiError(ApiResponse response) {
    String? errorCode;
    String message = 'Request failed (${response.statusCode})';
    try {
      final body = response.json;
      errorCode = body['error_code'] as String?;
      message = (body['message'] ?? body['detail'] ?? message).toString();
    } catch (_) {
      // Keep the status-derived message when the server did not return JSON.
    }
    if (errorCode == 'NON_CATTLE_IMAGE') {
      throw NonCattleImageException(message);
    }
    return ApiRequestException(
      response.statusCode,
      message,
      errorCode: errorCode,
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
            'model_version': result.modelVersion,
            'inference_mode': result.inferenceMode,
            'disease_scores': result.scores,
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
      throw _apiError(fusion);
    }
    final fusedClass = (fusion.json['disease_class'] ?? result.label) as String;
    if (!activeDetectionClasses.contains(fusedClass)) {
      throw const InvalidPredictionException('Invalid fused active class');
    }
    final fusedConfidence =
        ((fusion.json['confidence'] ?? result.confidence) as num).toDouble();
    return ScanResult(
      localId: fusion.json['id'] as String? ?? result.localId,
      cattleId: cattleId,
      label: fusedClass,
      confidence: fusedConfidence,
      capturedAt: result.capturedAt,
      inferenceMode: result.inferenceMode,
      syncStatus: 'synced',
      imagePath: result.imagePath,
      modelVersion: result.modelVersion,
      scores: result.scores,
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
        .cast<Map<String, dynamic>>()
        .where((item) => item['farmer_id'] == farmerId)
        .map(DetectionHistoryItem.fromJson)
        .toList();
  }

  Future<void> updateDetectionHistoryCattle({
    required String farmerId,
    required String resultId,
    String? cattleId,
  }) async {
    final response = await transport.send(
      ApiRequest(
        'PATCH',
        '/api/fusion/results/$resultId/cattle',
        body: jsonEncode({'farmer_id': farmerId, 'cattle_id': cattleId}),
        headers: {'Accept': 'application/json'},
      ),
    );
    if (response.statusCode != 200) {
      throw Exception('Update detection cattle failed');
    }
  }

  Future<void> deleteDetectionHistory({
    required String farmerId,
    required String resultId,
  }) async {
    final response = await transport.send(
      ApiRequest(
        'DELETE',
        '/api/fusion/results/$resultId?farmer_id=${Uri.encodeQueryComponent(farmerId)}',
      ),
    );
    if (response.statusCode != 200) {
      throw Exception('Delete detection history failed');
    }
  }
}
