import 'dart:convert';
import 'dart:io' show SocketException;

import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as image_lib;
import 'package:sapisehat_mobile/main.dart';
import 'package:sapisehat_mobile/features/scan/offline_inference.dart';

class _FailingPredictTransport implements ApiTransport {
  _FailingPredictTransport({this.modelNotReady = false});

  final bool modelNotReady;
  final requests = <ApiRequest>[];

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    requests.add(request);
    if (request.path == '/api/predict') {
      if (modelNotReady) {
        return ApiResponse(
          503,
          jsonEncode({
            'status': 'error',
            'error_code': 'MODEL_NOT_READY',
            'message': 'Model is not ready',
          }),
        );
      }
      throw const SocketException('network down');
    }
    if (request.path == '/api/fusion/results') {
      return ApiResponse(
        200,
        jsonEncode({'id': 'fusion-offline-1', 'disease_class': 'FMD'}),
      );
    }
    return ApiResponse(404, '{}');
  }
}

const _metadata = OfflineModelMetadata(
  modelVersion: 'fmd-mobilenetv3-test',
  classOrder: ['non_sapi', 'pmk', 'sehat'],
  inputSize: 224,
);

void main() {
  test('metadata contract uses the bilinear resize algorithm', () {
    expect(modelResizeInterpolation, image_lib.Interpolation.linear);
  });

  test('image quality gate reports small, dark, and blurry reasons', () {
    final image = image_lib.Image(width: 100, height: 100);
    final bytes = image_lib.encodePng(image);

    expect(
      () => validateImageQuality(bytes),
      throwsA(
        isA<ImageQualityException>().having(
          (error) => error.reasons,
          'reasons',
          containsAll([
            contains('terlalu kecil'),
            contains('terlalu gelap'),
            contains('terlalu buram'),
          ]),
        ),
      ),
    );
  });

  test(
    'offline inference maps active scores using metadata class order',
    () async {
      final service = OfflineInferenceService(
        metadata: _metadata,
        runModel: (_) async => [0.05, 0.90, 0.05],
      );

      final result = await service.infer([1, 2, 3]);

      expect(result.label, 'FMD');
      expect(result.modelVersion, 'fmd-mobilenetv3-test');
      expect(result.scores.keys, containsAll(<String>['FMD', 'healthy']));
      expect(result.scores, isNot(contains('non_cattle')));
      expect(result.scores.values.reduce((a, b) => a + b), closeTo(1, 0.001));
      expect(result.confidence, result.scores['FMD']);
    },
  );

  test(
    'offline inference rejects non-cattle before returning a result',
    () async {
      final service = OfflineInferenceService(
        metadata: _metadata,
        runModel: (_) async => [0.90, 0.05, 0.05],
      );

      expect(
        () => service.infer([1, 2, 3]),
        throwsA(isA<NonCattleImageException>()),
      );
    },
  );

  test('predictScan falls back when the backend is unavailable', () async {
    final api = SapiSehatApiClient(
      transport: _FailingPredictTransport(),
      offlineInferenceService: OfflineInferenceService(
        metadata: _metadata,
        runModel: (_) async => [0.05, 0.90, 0.05],
      ),
    );

    final result = await api.predictScan(bytes: [1, 2, 3]);

    expect(result.label, 'FMD');
    expect(result.inferenceMode, 'offline');
    expect(result.modelVersion, 'fmd-mobilenetv3-test');
  });

  test('model-not-ready reports an explicit unavailable reason', () async {
    final api = SapiSehatApiClient(
      transport: _FailingPredictTransport(modelNotReady: true),
      offlineInferenceService: OfflineInferenceService(
        metadata: _metadata,
        runModel: (_) async =>
            throw const FormatException('Offline model metadata is pending'),
      ),
    );

    expect(
      () => api.predictScan(bytes: [1, 2, 3]),
      throwsA(
        isA<DetectionUnavailableException>().having(
          (error) => error.message,
          'message',
          contains('belum siap'),
        ),
      ),
    );
  });

  test('saving offline result sends image-only active evidence', () async {
    final transport = _FailingPredictTransport();
    final api = SapiSehatApiClient(
      transport: transport,
      offlineInferenceService: OfflineInferenceService(
        metadata: _metadata,
        runModel: (_) async => [0.05, 0.90, 0.05],
      ),
    );

    final predicted = await api.predictScan(bytes: [1, 2, 3]);
    await api.saveScanResult(farmerId: 'farmer-1', result: predicted);

    final fusionBody =
        jsonDecode(transport.requests.last.body!) as Map<String, dynamic>;
    final evidence = fusionBody['image_evidence'] as Map<String, dynamic>;
    expect(evidence['inference_mode'], 'offline');
    expect(evidence['model_version'], 'fmd-mobilenetv3-test');
    expect(evidence['disease_scores'], predicted.scores);
    expect(fusionBody['nlp_evidence'], isNull);
  });
}
