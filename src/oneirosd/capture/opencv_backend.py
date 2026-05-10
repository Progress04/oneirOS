from datetime import datetime
import time
from typing import Optional

import cv2

from .base import CaptureBackend
from .types import FrameResult


class OpenCVCaptureBackend(CaptureBackend):
    @staticmethod
    def discover_cameras(max_index: int = 5) -> list[int]:
        """Return indices that can be opened as cameras."""
        available: list[int] = []
        for idx in range(max_index + 1):
            capture = cv2.VideoCapture(idx)
            try:
                if capture is not None and capture.isOpened():
                    available.append(idx)
            finally:
                if capture is not None:
                    capture.release()
        return available

    def __init__(
        self,
        camera_index: int = 0,
        width: Optional[int] = None,
        height: Optional[int] = None,
        backend: Optional[int] = None,
    ) -> None:
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.backend = backend
        self._capture: Optional[cv2.VideoCapture] = None

    def open(self) -> None:
        if self.backend is not None:
            self._capture = cv2.VideoCapture(self.camera_index, self.backend)
        else:
            self._capture = cv2.VideoCapture(self.camera_index)

        if self._capture is None or not self._capture.isOpened():
            # Keep handle so release() stays safe/idempotent.
            return

        if self.width is not None:
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)

        if self.height is not None:
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Warm up the sensor/auto-exposure pipeline to avoid initial black frames.
        for _ in range(5):
            self._capture.grab()
            time.sleep(0.03)

    def is_opened(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def capture_frame(self) -> FrameResult:
        timestamp = datetime.now()

        if not self.is_opened():
            return FrameResult(
                frame=None,
                success=False,
                timestamp=timestamp,
                camera_index=self.camera_index,
                error="Camera is not opened.",
            )

        frame = None
        for _ in range(6):
            ok, candidate = self._capture.read()
            if not ok or candidate is None:
                time.sleep(0.03)
                continue

            # Retry when frame is essentially black (common during camera startup).
            if float(candidate.mean()) < 2.0:
                time.sleep(0.03)
                continue

            frame = candidate
            break

        if frame is None:
            return FrameResult(
                frame=None,
                success=False,
                timestamp=timestamp,
                camera_index=self.camera_index,
                error="Failed to read a valid frame from camera.",
            )

        height, width = frame.shape[:2]
        return FrameResult(
            frame=frame,
            success=True,
            timestamp=timestamp,
            camera_index=self.camera_index,
            width=width,
            height=height,
        )

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def __enter__(self) -> "OpenCVCaptureBackend":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()
