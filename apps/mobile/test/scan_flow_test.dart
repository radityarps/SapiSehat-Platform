import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/main.dart';

class ScanTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/predict') {
      return ApiResponse(200, jsonEncode({
        'status': 'success',
        'prediction': {
          'disease_class': 'FMD',
          'confidence': 0.82,
          'is_reliable': true,
          'scores': {'FMD': 0.82, 'LSD': 0.08, 'healthy': 0.10},
        },
        'model_info': {'version': '1.0.0'},
      }));
    }
    if (request.path == '/api/media/uploads') {
      return ApiResponse(200, jsonEncode({
        'id': 'media-1',
        'farmer_id': 'farmer-1',
        'cattle_id': 'cattle-1',
        'storage_reference': 'scan-images/farmer-1/2026/06/media-1.jpg',
      }));
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  test('camera scan classifies image then stores scan media metadata', () async {
    final transport = ScanTransport();
    final api = SapiSehatApiClient(transport: transport);

    final result = await api.uploadScan(
      farmerId: 'farmer-1',
      cattleId: 'cattle-1',
      bytes: [1, 2, 3, 4],
    );

    expect(result.label, 'FMD');
    expect(result.confidence, 0.82);
    expect(result.inferenceMode, 'online');
    expect(result.syncStatus, 'synced');
    expect(transport.requests.map((request) => request.path), [
      '/api/predict',
      '/api/media/uploads',
    ]);
    expect(transport.requests.first.body, contains('image-bytes'));
    expect(transport.requests.last.body, contains('multipart-image'));
  });
}
