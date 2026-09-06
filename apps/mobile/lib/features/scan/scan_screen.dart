import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../core/api_client.dart';
import '../../features/auth/auth.dart';
import '../cattle/cattle.dart';
import 'offline_inference.dart';
import 'scan.dart';
import 'scan_result_detail_page.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({
    super.key,
    required this.apiClient,
    required this.session,
    required this.onScan,
  });
  final SapiSehatApiClient apiClient;
  final AccountSession session;
  final ValueChanged<ScanResult> onScan;
  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  final picker = ImagePicker();
  CameraController? cameraController;
  List<CattleProfile> cattle = [];
  XFile? selectedImage;
  bool loading = false;
  bool cameraLoading = true;
  bool showGrid = true;
  FlashMode flashMode = FlashMode.auto;
  String? error;

  @override
  void initState() {
    super.initState();
    loadCattle();
    initCamera();
  }

  @override
  void dispose() {
    cameraController?.dispose().catchError((_) {});
    super.dispose();
  }

  Future<bool> ensureCameraPermission() async {
    final status = await Permission.camera.status;
    if (status.isGranted) return true;

    if (status.isPermanentlyDenied || status.isRestricted) {
      if (!mounted) return false;
      setState(() => cameraLoading = false);
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Izin kamera ditolak'),
          content: const Text(
            'Buka pengaturan aplikasi untuk mengizinkan akses kamera.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Batal'),
            ),
            FilledButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
                openAppSettings();
              },
              child: const Text('Pengaturan'),
            ),
          ],
        ),
      );
      return false;
    }

    if (!mounted) return false;
    setState(() => cameraLoading = false);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Izin kamera diperlukan'),
        content: const Text(
          'SapiSehat membutuhkan izin kamera untuk mengambil gambar sapi di dalam aplikasi.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Izinkan'),
          ),
        ],
      ),
    );
    if (confirmed != true) return false;
    if (mounted) setState(() => cameraLoading = true);
    final requested = await Permission.camera.request();
    if (requested.isGranted) return true;
    if (!mounted) return false;
    setState(() {
      cameraLoading = false;
      error = 'Izin kamera ditolak.';
    });
    return false;
  }

  Future<void> initCamera() async {
    if (!mounted) return;
    setState(() {
      cameraLoading = true;
      error = null;
    });
    try {
      final allowed = await ensureCameraPermission();
      if (!allowed) return;
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        throw StateError('No camera available');
      }
      final backCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
      await cameraController?.dispose().catchError((_) {});
      final controller = CameraController(
        backCamera,
        ResolutionPreset.medium,
        enableAudio: false,
      );
      await controller.initialize();
      await controller.setFlashMode(flashMode);
      if (!mounted) return;
      setState(() {
        cameraController = controller;
        cameraLoading = false;
      });
    } on CameraException catch (exc) {
      if (!mounted) return;
      setState(() {
        cameraLoading = false;
        error = exc.code == 'CameraAccessDenied'
            ? 'Izin kamera ditolak.'
            : 'Kamera tidak bisa dibuka. Gunakan galeri atau periksa izin kamera.';
      });
    } on PlatformException {
      if (!mounted) return;
      setState(() {
        cameraLoading = false;
        error =
            'Kamera belum siap. Tutup aplikasi lalu buka kembali, atau gunakan galeri.';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        cameraLoading = false;
        error =
            'Kamera tidak bisa dibuka. Gunakan galeri atau periksa izin kamera.';
      });
    }
  }

  Future<void> loadCattle() async {
    try {
      final items = await widget.apiClient.listCattle(widget.session.farmerId);
      if (!mounted) return;
      setState(() => cattle = items);
    } catch (_) {
      if (!mounted) return;
      setState(() => error = 'Gagal memuat daftar sapi.');
    }
  }

  Future<void> captureInApp() async {
    var controller = cameraController;
    if (controller == null || !controller.value.isInitialized) {
      await initCamera();
      if (!mounted) return;
      controller = cameraController;
      if (controller == null || !controller.value.isInitialized) {
        setState(() => error = 'Kamera belum siap.');
        return;
      }
    }
    if (loading) return;
    setState(() {
      error = null;
      loading = true;
    });
    try {
      final file = await controller.takePicture();
      await predictAndOpen(file);
    } catch (_) {
      if (!mounted) return;
      setState(() => error = 'Gagal mengambil gambar.');
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> pickGallery() async {
    if (loading) return;
    setState(() => error = null);
    final file = await picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
    );
    if (file == null) return;
    setState(() => loading = true);
    try {
      await predictAndOpen(file);
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> predictAndOpen(XFile file) async {
    setState(() => selectedImage = file);
    try {
      final bytes = await file.readAsBytes();
      validateImageQuality(bytes);
      final prediction = await widget.apiClient.predictScan(bytes: bytes);
      final scan = ScanResult(
        localId: prediction.localId,
        cattleId: prediction.cattleId,
        label: prediction.label,
        confidence: prediction.confidence,
        capturedAt: prediction.capturedAt,
        inferenceMode: prediction.inferenceMode,
        syncStatus: prediction.syncStatus,
        imagePath: file.path,
        modelVersion: prediction.modelVersion,
        scores: prediction.scores,
      );
      if (!mounted) return;
      final saved = await Navigator.of(context).push<ScanResult?>(
        MaterialPageRoute(
          builder: (_) => ScanResultDetailPage(
            apiClient: widget.apiClient,
            session: widget.session,
            result: scan,
            image: file,
            cattle: cattle,
          ),
        ),
      );
      if (saved != null) widget.onScan(saved);
    } on ImageQualityException catch (exception) {
      await showDetectionFailure(
        title: 'Kualitas gambar belum cukup',
        message: exception.message,
      );
    } on NonCattleImageException catch (exception) {
      await showDetectionFailure(
        title: 'Gambar bukan sapi',
        message: exception.message,
      );
    } on DetectionUnavailableException catch (exception) {
      await showDetectionFailure(
        title: 'Deteksi belum tersedia',
        message: exception.message,
      );
    } on ApiRequestException catch (exception) {
      await showDetectionFailure(
        title: 'Deteksi gagal',
        message: exception.message,
      );
    } catch (exception) {
      await showDetectionFailure(
        title: 'Deteksi gagal',
        message: 'Gambar tidak dapat diproses. Coba ambil gambar ulang.',
      );
    }
  }

  Future<void> showDetectionFailure({
    required String title,
    required String message,
  }) async {
    if (!mounted) return;
    setState(() => error = message);
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Ambil ulang'),
          ),
        ],
      ),
    );
  }

  Future<void> cycleFlash() async {
    final next = switch (flashMode) {
      FlashMode.auto => FlashMode.always,
      FlashMode.always => FlashMode.off,
      _ => FlashMode.auto,
    };
    setState(() => flashMode = next);
    await cameraController?.setFlashMode(next);
  }

  @override
  Widget build(BuildContext context) => Stack(
    fit: StackFit.expand,
    children: [
      _CameraBackground(
        controller: cameraController,
        loading: cameraLoading,
        lastImage: selectedImage,
      ),
      if (showGrid) const _GridOverlay(),
      _TopCopy(error: error),
      _TopControls(
        flashMode: flashMode,
        showGrid: showGrid,
        onFlash: cycleFlash,
        onGrid: () => setState(() => showGrid = !showGrid),
      ),
      _BottomControls(
        loading: loading,
        onGallery: pickGallery,
        onCapture: captureInApp,
      ),
      if (loading)
        const Align(
          alignment: Alignment.bottomCenter,
          child: LinearProgressIndicator(),
        ),
    ],
  );
}

class _CameraBackground extends StatelessWidget {
  const _CameraBackground({
    required this.controller,
    required this.loading,
    required this.lastImage,
  });
  final CameraController? controller;
  final bool loading;
  final XFile? lastImage;

  @override
  Widget build(BuildContext context) {
    final camera = controller;
    if (camera != null && camera.value.isInitialized) {
      return ClipRect(
        child: FittedBox(
          fit: BoxFit.cover,
          child: SizedBox(
            width:
                camera.value.previewSize?.height ??
                MediaQuery.sizeOf(context).width,
            height:
                camera.value.previewSize?.width ??
                MediaQuery.sizeOf(context).height,
            child: CameraPreview(camera),
          ),
        ),
      );
    }
    if (lastImage != null) {
      return Image.file(File(lastImage!.path), fit: BoxFit.cover);
    }
    return Container(
      color: Colors.black,
      child: Center(
        child: loading
            ? const CircularProgressIndicator(color: Colors.white)
            : const Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.camera_alt, color: Colors.white70, size: 64),
                  SizedBox(height: 12),
                  Text(
                    'Kamera belum siap',
                    style: TextStyle(color: Colors.white70),
                  ),
                ],
              ),
      ),
    );
  }
}

class _TopCopy extends StatelessWidget {
  const _TopCopy({this.error});
  final String? error;
  @override
  Widget build(BuildContext context) => Positioned(
    top: 28,
    left: 20,
    right: 86,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Periksa sapi',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            color: Colors.white,
            fontWeight: FontWeight.w900,
            shadows: const [Shadow(blurRadius: 8)],
          ),
        ),
        const SizedBox(height: 6),
        const Text(
          'Arahkan kamera ke sapi. Hasil akan terbuka di halaman detail.',
          style: TextStyle(
            color: Colors.white,
            shadows: [Shadow(blurRadius: 8)],
          ),
        ),
        if (error != null)
          Padding(
            padding: const EdgeInsets.only(top: 10),
            child: Text(
              error!,
              style: const TextStyle(
                color: Color(0xFFFFD8A8),
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
      ],
    ),
  );
}

class _TopControls extends StatelessWidget {
  const _TopControls({
    required this.flashMode,
    required this.showGrid,
    required this.onFlash,
    required this.onGrid,
  });
  final FlashMode flashMode;
  final bool showGrid;
  final VoidCallback onFlash;
  final VoidCallback onGrid;
  @override
  Widget build(BuildContext context) => Positioned(
    top: 34,
    right: 12,
    child: Column(
      children: [
        _CircleTool(icon: _flashIcon(flashMode), onTap: onFlash),
        const SizedBox(height: 8),
        _CircleTool(
          icon: showGrid ? Icons.grid_on : Icons.grid_off,
          onTap: onGrid,
        ),
      ],
    ),
  );
  IconData _flashIcon(FlashMode mode) => switch (mode) {
    FlashMode.always => Icons.flash_on,
    FlashMode.off => Icons.flash_off,
    _ => Icons.flash_auto,
  };
}

class _BottomControls extends StatelessWidget {
  const _BottomControls({
    required this.loading,
    required this.onGallery,
    required this.onCapture,
  });
  final bool loading;
  final VoidCallback onGallery;
  final VoidCallback onCapture;
  @override
  Widget build(BuildContext context) => Positioned(
    left: 32,
    right: 32,
    bottom: 34,
    child: Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _CircleTool(
          icon: Icons.photo_library_outlined,
          onTap: loading ? null : onGallery,
          size: 54,
        ),
        GestureDetector(
          onTap: loading ? null : onCapture,
          child: Container(
            width: 82,
            height: 82,
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 4),
            ),
            child: Container(
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: Color(0xFF2E6B4F),
              ),
            ),
          ),
        ),
        const SizedBox(width: 54),
      ],
    ),
  );
}

class _GridOverlay extends StatelessWidget {
  const _GridOverlay();
  @override
  Widget build(BuildContext context) =>
      IgnorePointer(child: CustomPaint(painter: _GridPainter()));
}

class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withValues(alpha: 0.28)
      ..strokeWidth = 1;
    canvas.drawLine(
      Offset(0, size.height / 3),
      Offset(size.width, size.height / 3),
      paint,
    );
    canvas.drawLine(
      Offset(0, size.height * 2 / 3),
      Offset(size.width, size.height * 2 / 3),
      paint,
    );
    canvas.drawLine(
      Offset(size.width / 3, 0),
      Offset(size.width / 3, size.height),
      paint,
    );
    canvas.drawLine(
      Offset(size.width * 2 / 3, 0),
      Offset(size.width * 2 / 3, size.height),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _CircleTool extends StatelessWidget {
  const _CircleTool({required this.icon, required this.onTap, this.size = 46});
  final IconData icon;
  final VoidCallback? onTap;
  final double size;
  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onTap,
    borderRadius: BorderRadius.circular(size / 2),
    child: Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.black.withValues(alpha: 0.42),
      ),
      child: Icon(icon, color: Colors.white),
    ),
  );
}
