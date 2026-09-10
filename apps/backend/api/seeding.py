"""Environment-aware data seeding.

Seed tiers (config.resolved_seed_tier):
  - production:  master admin account only.
  - staging:     master admin + district officer + 2 farmer accounts.
  - development: staging accounts + sample cattle, detections, and risk signals.

Account seeding is handled lazily on login by surface_auth.seed_default_*.
This module adds the development-only sample operational data, created
through the real API flow so records are valid and scope-correct.
"""

from __future__ import annotations

def seed_development_sample_data() -> None:
    """Operational sample data seeding has been removed."""
    pass
