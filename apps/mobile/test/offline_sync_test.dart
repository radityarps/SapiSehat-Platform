import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/main.dart';

class OfflineSyncTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/offline/detections/sync') {
      return ApiResponse(200, jsonEncode({
        'local_detection_id': jsonDecode(request.body!)['local_detection_id'],
        'sync_status': 'synced',
        'local_created_at': jsonDecode(request.body!)['local_created_at'],
      }));
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  test('offline fallback sync preserves local id and original capture time', () async {
    final transport = OfflineSyncTransport();
    final api = SapiSehatApiClient(transport: transport);
    final capturedAt = DateTime.parse('2026-06-05T08:30:00+07:00');
    final detection = PendingOfflineDetection(
      localId: 'local-abc',
      farmerId: 'farmer-1',
      cattleId: 'cattle-1',
      localCreatedAt: capturedAt,
      label: 'FMD',
      confidence: 0.8,
    );

    await api.syncOffline(detection);

    final payload = jsonDecode(transport.requests.single.body!) as Map<String, dynamic>;
    expect(transport.requests.single.path, '/api/offline/detections/sync');
    expect(payload['local_detection_id'], 'local-abc');
    expect(payload['local_created_at'], capturedAt.toIso8601String());
    expect(payload['image_evidence']['inference_mode'], 'offline');
    expect(payload['image_evidence']['model_version'], 'image-offline-1.0.0');
    expect(payload['nlp_evidence']['inference_mode'], 'offline');
    expect(payload['offline_fused_result']['disease_class'], 'FMD');
  });
}
