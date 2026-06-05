"""Custom exceptions for the application."""

from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for API error responses."""
    INVALID_IMAGE = "INVALID_IMAGE"
    MODEL_NOT_READY = "MODEL_NOT_READY"
    INFERENCE_FAILED = "INFERENCE_FAILED"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"


class SapiSehatException(Exception):
    """Base exception for SapiSehat application."""
    pass


class ModelLoadError(SapiSehatException):
    """Raised when model fails to load."""
    pass


class PreprocessingError(SapiSehatException):
    """Raised when image preprocessing fails."""
    pass


class InferenceError(SapiSehatException):
    """Raised when model inference fails."""
    pass


class InvalidImageError(SapiSehatException):
    """Raised when image is invalid or unsupported."""
    pass
