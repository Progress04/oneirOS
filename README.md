# oneirOS / oneirOSD

A lightweight local background app that detects when the user may have fallen asleep while watching a show or movie, using periodic webcam frame sampling. The app runs locally, avoids recording video, and can trigger a safe system action such as locking, suspending, or shutting down the computer after a confirmation period and cancel countdown.

## Core idea

oneirOS is not a continuous video surveillance app. It should be a low-power daemon that periodically captures still frames from the webcam. In idle mode, it checks infrequently. If the user's eyes appear closed, it temporarily enters a higher-frequency confirmation mode. If sustained eye closure is detected, it displays a countdown that allows the user to cancel before performing an action.

Initial target platform: macOS on a MacBook.

Future target platform: Windows.

Design the code so Windows support can be added later by swapping platform-specific backends, not by rewriting the app.

---

## MVP goal

Build a working macOS-first prototype that:

1. Runs from the command line.
2. Opens the default webcam.
3. Captures a single frame on demand.
4. Supports periodic frame capture in idle mode.
5. Has a clean capture abstraction so Windows support can be added later.
6. Does not save images or video by default.
7. Logs only simple runtime events.
8. Is ready for later integration with an eye-closure detector and sleep state machine.

The first implementation should focus only on the capture layer.

---

## High-level architecture

```text
oneirOS
  ├── Capture Layer
  │     ├── camera discovery
  │     ├── open camera
  │     ├── capture still frame
  │     ├── release camera
  │     └── return frame metadata
  │
  ├── Detection Layer
  │     ├── face detection
  │     ├── eye detection
  │     └── eye-closure confidence
  │
  ├── State Layer
  │     ├── idle mode
  │     ├── confirmation mode
  │     ├── sleep decision logic
  │     └── false-positive prevention
  │
  ├── Action Layer
  │     ├── countdown
  │     ├── cancel action
  │     ├── lock screen
  │     ├── suspend
  │     └── shutdown
  │
  ├── Config Layer
  │     ├── timing settings
  │     ├── camera settings
  │     ├── action settings
  │     └── CPU/GPU settings
  │
  └── Logging / Privacy Layer
        ├── event logs
        ├── no video storage
        └── no image storage by default
```

For now, only implement the **Capture Layer**.

---

## Capture layer design

The capture layer should hide camera implementation details from the rest of the app.

The rest of the codebase should not directly call OpenCV. Instead, it should depend on a generic `CaptureBackend` interface.

This allows the app to start with OpenCV on macOS, then later add:

* a macOS AVFoundation-specific backend if needed
* a Windows Media Foundation backend if needed
* a mock backend for testing

---

## Recommended initial package structure

```text
oneiros/
  pyproject.toml
  README.md
  src/
    oneirosd/
      __init__.py
      main.py
      capture/
        __init__.py
        base.py
        types.py
        opencv_backend.py
      config/
        __init__.py
        settings.py
      logging_utils/
        __init__.py
        logger.py
  tests/
    test_capture_types.py
    test_mock_capture.py
```

Use `oneirosd` as the daemon/runtime package name.

---

## Capture layer files

### `src/oneirosd/capture/types.py`

Define a frame result object.

```python
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
```

### `src/oneirosd/capture/base.py`

Define the capture backend interface.

```python
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
```

### `src/oneirosd/capture/opencv_backend.py`

Implement the first backend using OpenCV.

Requirements:

* Use `cv2.VideoCapture`.
* Default to camera index `0`.
* Allow optional width and height.
* Return `FrameResult` instead of raw frames.
* Do not save images by default.
* Always release the camera cleanly.
* Handle camera permission failures gracefully.

Suggested implementation shape:

```python
from datetime import datetime
from typing import Optional

import cv2

from .base import CaptureBackend
from .types import FrameResult


class OpenCVCaptureBackend(CaptureBackend):
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

        if self.width is not None:
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)

        if self.height is not None:
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

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

        ok, frame = self._capture.read()

        if
```
