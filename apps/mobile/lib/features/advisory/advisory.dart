import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../auth/auth.dart';

class AreaAdvisoryBanner extends StatefulWidget {
  const AreaAdvisoryBanner({
    super.key,
    required this.apiClient,
    required this.session,
  });

  final SapiSehatApiClient apiClient;
  final AccountSession session;

  @override
  State<AreaAdvisoryBanner> createState() => _AreaAdvisoryBannerState();
}

class _AreaAdvisoryBannerState extends State<AreaAdvisoryBanner> {
  late Future<FarmerAreaAdvisory> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.apiClient.getAreaAdvisory(widget.session);
  }

  @override
  void didUpdateWidget(covariant AreaAdvisoryBanner oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.session.farmerId != widget.session.farmerId ||
        oldWidget.apiClient != widget.apiClient) {
      _future = widget.apiClient.getAreaAdvisory(widget.session);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<FarmerAreaAdvisory>(
      future: _future,
      builder: (context, snapshot) {
        final advisory = snapshot.data;
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const _AdvisoryLoadingCard();
        }
        if (snapshot.hasError || advisory == null || !advisory.advisoryActive) {
          return const SizedBox.shrink();
        }
        return _ActiveAdvisoryCard(advisory: advisory);
      },
    );
  }
}

class _AdvisoryLoadingCard extends StatelessWidget {
  const _AdvisoryLoadingCard();

  @override
  Widget build(BuildContext context) => Container(
    height: 56,
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      borderRadius: BorderRadius.circular(14),
    ),
  );
}

class _ActiveAdvisoryCard extends StatelessWidget {
  const _ActiveAdvisoryCard({required this.advisory});

  final FarmerAreaAdvisory advisory;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Semantics(
      label: 'Imbauan risiko area',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: colorScheme.errorContainer.withValues(alpha: 0.82),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: colorScheme.error.withValues(alpha: 0.28)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              Icons.warning_amber_rounded,
              color: colorScheme.error,
              size: 22,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Imbauan area',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      color: colorScheme.onErrorContainer,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Ada peningkatan laporan risiko penyakit di kecamatan Anda. Pantau sapi, perkuat biosekuriti, dan hubungi petugas kesehatan hewan jika muncul gejala.',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: colorScheme.onErrorContainer,
                      height: 1.35,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Berlaku untuk tingkat kecamatan. Tidak menampilkan data peternak lain.',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: colorScheme.onErrorContainer.withValues(alpha: 0.78),
                      height: 1.3,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
