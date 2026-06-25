import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key, required this.onFinished});
  final VoidCallback onFinished;
  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final controller = PageController();
  var page = 0;
  bool get isLast => page == _slides.length - 1;

  Future<void> next() async {
    if (isLast) return widget.onFinished();
    await controller.animateToPage(
      page + 1,
      duration: const Duration(milliseconds: 260),
      curve: Curves.easeOutCubic,
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 16, 0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Text(
                      'SapiSehat',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                        color: const Color(0xFF2E6B4F),
                      ),
                    ),
                  ],
                ),
                TextButton(
                  onPressed: widget.onFinished,
                  child: const Text(
                    'Lewati',
                    style: TextStyle(color: Color(0xFF687266)),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: PageView.builder(
              controller: controller,
              itemCount: _slides.length,
              onPageChanged: (value) => setState(() => page = value),
              itemBuilder: (context, index) =>
                  _SlideView(slide: _slides[index]),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                for (var i = 0; i < _slides.length; i++)
                  _Dot(active: i == page),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: SizedBox(
              width: double.infinity,
              height: 56,
              child: FilledButton(
                onPressed: next,
                style: FilledButton.styleFrom(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: Text(isLast ? 'Mulai pakai SapiSehat' : 'Lanjut'),
              ),
            ),
          ),
          const SizedBox(height: 32),
        ],
      ),
    ),
  );
}

class _Slide {
  const _Slide({required this.asset, required this.title, required this.body});
  final String asset;
  final String title;
  final String body;
}

const _slides = [
  _Slide(
    asset: 'assets/onboarding/veterinary-clinic.svg',
    title: 'Kelola kesehatan sapi',
    body:
        'Gunakan kamera untuk mencatat sinyal risiko PMK dan LSD. Hasil bukan diagnosis veteriner.',
  ),
  _Slide(
    asset: 'assets/onboarding/undraw_no-signal_nqfa.svg',
    title: 'Mode offline tersedia',
    body:
        'Pencatatan tetap berjalan tanpa internet memakai model di perangkat, lalu sinkron saat koneksi kembali.',
  ),
  _Slide(
    asset: 'assets/onboarding/undraw_correct-answer_vjt7.svg',
    title: 'Riwayat & tindak lanjut',
    body:
        'Simpan riwayat pemeriksaan per sapi dan gunakan informasi aman untuk prioritas tindak lanjut.',
  ),
];

class _SlideView extends StatelessWidget {
  const _SlideView({required this.slide});
  final _Slide slide;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 32),
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        SvgPicture.asset(
          slide.asset,
          height: MediaQuery.sizeOf(context).height * 0.32,
          fit: BoxFit.contain,
        ),
        const SizedBox(height: 32),
        Text(
          slide.title,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.w900,
            color: const Color(0xFF1F2A21),
          ),
        ),
        const SizedBox(height: 12),
        Text(
          slide.body,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
            color: const Color(0xFF687266),
            height: 1.45,
          ),
        ),
      ],
    ),
  );
}

class _Dot extends StatelessWidget {
  const _Dot({required this.active});
  final bool active;
  @override
  Widget build(BuildContext context) => AnimatedContainer(
    duration: const Duration(milliseconds: 220),
    margin: const EdgeInsets.symmetric(horizontal: 4),
    height: 8,
    width: active ? 24 : 8,
    decoration: BoxDecoration(
      color: active ? const Color(0xFF2E6B4F) : const Color(0xFFD8D6CB),
      borderRadius: BorderRadius.circular(4),
    ),
  );
}
