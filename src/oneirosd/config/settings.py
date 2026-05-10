from dataclasses import dataclass
from typing import Optional


@dataclass
class CaptureSettings:
    camera_index: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    backend: Optional[int] = None
    idle_interval_seconds: float = 15.0
