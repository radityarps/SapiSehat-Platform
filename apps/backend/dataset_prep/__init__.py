"""
Dataset preparation package for the SapiSehat cattle disease classifier.

Provides reproducible dataset splitting, duplicate detection, label
validation, and audit-report generation for the canonical 3-class problem
(FMD / LSD / healthy).

This package does NOT download, commit, or train on real dataset images.
It operates on a user-provided dataset path supplied at runtime.
"""

from .core import (
    CANONICAL_CLASSES,
    CLASS_ALIASES,
    normalize_class_name,
    discover_images,
    compute_file_hash,
    compute_perceptual_hash,
    PERCEPTUAL_HASH_BACKEND,
    group_exact_duplicates,
    group_near_duplicates,
    stratified_split,
    compute_class_weights,
    ImageRecord,
)

__all__ = [
    "CANONICAL_CLASSES",
    "CLASS_ALIASES",
    "normalize_class_name",
    "discover_images",
    "compute_file_hash",
    "compute_perceptual_hash",
    "PERCEPTUAL_HASH_BACKEND",
    "group_exact_duplicates",
    "group_near_duplicates",
    "stratified_split",
    "compute_class_weights",
    "ImageRecord",
]
