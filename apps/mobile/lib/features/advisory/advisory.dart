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
    margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
    height: 72,
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      borderRadius: BorderRadius.circular(16),
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
      label: 'Area risk advisory',
      child: Container(
        margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: colorScheme.secondaryContainer,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: colorScheme.outlineVariant),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.info_outline, color: colorScheme.onSecondaryContainer),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Imbauan area',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: colorScheme.onSecondaryContainer,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    advisory.message,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: colorScheme.onSecondaryContainer,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Berlaku untuk tingkat kecamatan. Tidak menampilkan data peternak lain.',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: colorScheme.onSecondaryContainer,
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
