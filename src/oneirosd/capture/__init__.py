"""Capture layer interfaces and backends."""

from .base import CaptureBackend
from .opencv_backend import OpenCVCaptureBackend
from .types import FrameResult

__all__ = ["CaptureBackend", "OpenCVCaptureBackend", "FrameResult"]
