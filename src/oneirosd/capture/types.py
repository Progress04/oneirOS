from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np


@dataclass
class FrameResult:
    frame: Optional[np.ndarray]
    success: bool
    timestamp: datetime
    camera_index: int
    width: Optional[int] = None
    height: Optional[int] = None
    error: Optional[str] = None
