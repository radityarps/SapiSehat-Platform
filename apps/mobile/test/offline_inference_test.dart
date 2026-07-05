import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:sapisehat_mobile/main.dart';
import 'package:sapisehat_mobile/features/scan/offline_inference.dart';

class _FailingPredictTransport implements ApiTransport {
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/predict') {
      throw Exception('network down');
    }
    if (request.path == '/api/fusion/results') {
      return ApiResponse(
        200,
        jsonEncode({
          'id': 'fusion-offline-1',
          'disease_class': 'LSD',
          'confidence': 0.9,
        }),
      );
    }
    return ApiResponse(404, '{}');
  }
}

void main() {
  test(
    'offline inference maps model scores using metadata class order',
    () async {
      final service = OfflineInferenceService(
        metadata: const OfflineModelMetadata(
          modelVersion: 'cattle-disease-mobilenetv2-test-dynamic-range',
          classOrder: ['FMD', 'LSD', 'healthy'],
          inputSize: 224,
        ),
        runModel: (_) async => [0.05, 0.90, 0.05],
      );

      final result = await service.infer([1, 2, 3]);

      expect(result.label, 'LSD');
      expect(result.confidence, 0.9);
      expect(
        result.modelVersion,
        'cattle-disease-mobilenetv2-test-dynamic-range',
      );
      expect(result.scores, {'FMD': 0.05, 'LSD': 0.9, 'healthy': 0.05});
    },
  );

  test(
    'predictScan falls back to mobile TFLite service when backend fails',
    () async {
      final transport = _FailingPredictTransport();
      final offlineService = OfflineInferenceService(
        metadata: const OfflineModelMetadata(
          modelVersion: 'cattle-disease-mobilenetv2-test-dynamic-range',
          classOrder: ['FMD', 'LSD', 'healthy'],
          inputSize: 224,
        ),
        runModel: (_) async => [0.05, 0.90, 0.05],
      );
      final api = SapiSehatApiClient(
        transport: transport,
        offlineInferenceService: offlineService,
      );

      final result = await api.predictScan(bytes: [1, 2, 3]);

      expect(result.label, 'LSD');
      expect(result.confidence, 0.9);
      expect(result.inferenceMode, 'offline');
      expect(
        result.modelVersion,
        'cattle-disease-mobilenetv2-test-dynamic-range',
      );
      expect(result.scores, {'FMD': 0.05, 'LSD': 0.9, 'healthy': 0.05});
    },
  );

  test('saving offline result preserves offline model metadata', () async {
    final transport = _FailingPredictTransport();
    final offlineService = OfflineInferenceService(
      metadata: const OfflineModelMetadata(
        modelVersion: 'cattle-disease-mobilenetv2-test-dynamic-range',
        classOrder: ['FMD', 'LSD', 'healthy'],
        inputSize: 224,
      ),
      runModel: (_) async => [0.05, 0.90, 0.05],
    );
    final api = SapiSehatApiClient(
      transport: transport,
      offlineInferenceService: offlineService,
    );

    final predicted = await api.predictScan(bytes: [1, 2, 3]);
    await api.saveScanResult(farmerId: 'farmer-1', result: predicted);

    final fusionBody =
        jsonDecode(transport.requests.last.body!) as Map<String, dynamic>;
    final evidence = fusionBody['image_evidence'] as Map<String, dynamic>;
    expect(evidence['inference_mode'], 'offline');
    expect(
      evidence['model_version'],
      'cattle-disease-mobilenetv2-test-dynamic-range',
    );
    expect(evidence['disease_scores'], {
      'FMD': 0.05,
      'LSD': 0.9,
      'healthy': 0.05,
    });
  });
}
