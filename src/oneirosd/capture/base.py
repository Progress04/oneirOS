from abc import ABC, abstractmethod

from .types import FrameResult


class CaptureBackend(ABC):
    @abstractmethod
    def open(self) -> None:
        """Open the camera resource."""
        raise NotImplementedError

    @abstractmethod
    def capture_frame(self) -> FrameResult:
        """Capture and return a single frame."""
        raise NotImplementedError

    @abstractmethod
    def release(self) -> None:
        """Release the camera resource."""
        raise NotImplementedError

    @abstractmethod
    def is_opened(self) -> bool:
        """Return whether the camera is currently open."""
        raise NotImplementedError
