import argparse
import time

import cv2

from .capture.opencv_backend import OpenCVCaptureBackend
from .logging_utils.logger import configure_logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="oneirosd capture layer CLI")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument(
        "--mode",
        choices=["once", "idle"],
        default="once",
        help="once: capture one frame, idle: periodic capture loop",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=15.0,
        help="capture interval when mode=idle",
    )
    parser.add_argument(
        "--discover-cameras",
        action="store_true",
        help="list likely available camera indices and exit",
    )
    parser.add_argument(
        "--request-camera-permission",
        action="store_true",
        help="open/release camera only to trigger OS permission prompt, then exit",
    )
    parser.add_argument(
        "--save-path",
        type=str,
        default=None,
        help="optional path to save a captured frame when mode=once",
    )
    return parser


def run_once(backend: OpenCVCaptureBackend) -> int:
    result = backend.capture_frame()
    if not result.success:
        return 1
    return 0


def run_idle(backend: OpenCVCaptureBackend, interval_seconds: float, logger) -> int:
    logger.info("Starting idle capture loop at %.2fs interval", interval_seconds)
    try:
        while True:
            result = backend.capture_frame()
            if result.success:
                logger.info(
                    "Captured frame camera=%s resolution=%sx%s",
                    result.camera_index,
                    result.width,
                    result.height,
                )
            else:
                logger.warning("Capture failed: %s", result.error)
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("Idle capture loop interrupted by user")
        return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logger = configure_logger()
    if args.discover_cameras:
        cameras = OpenCVCaptureBackend.discover_cameras()
        logger.info("Discovered cameras: %s", cameras if cameras else "none")
        return 0

    backend = OpenCVCaptureBackend(
        camera_index=args.camera_index,
        width=args.width,
        height=args.height,
    )

    backend.open()

    if args.request_camera_permission:
        if backend.is_opened():
            logger.info(
                "Camera permission appears granted for camera index %s.",
                args.camera_index,
            )
            backend.release()
            return 0

        logger.error(
            "Camera could not be opened. If permission prompt appeared, grant access and retry."
        )
        backend.release()
        return 2

    if not backend.is_opened():
        logger.error(
            "Unable to open camera index %s. Check camera permissions and availability.",
            args.camera_index,
        )
        backend.release()
        return 2

    try:
        if args.mode == "once":
            result = backend.capture_frame()
            if result.success:
                if args.save_path:
                    wrote = cv2.imwrite(args.save_path, result.frame)
                    if wrote:
                        logger.info("Saved frame to %s", args.save_path)
                    else:
                        logger.error("Failed to save frame to %s", args.save_path)
                        return 1
                logger.info(
                    "Captured frame camera=%s resolution=%sx%s",
                    result.camera_index,
                    result.width,
                    result.height,
                )
                return 0

            logger.error("Capture failed: %s", result.error)
            return 1

        return run_idle(backend, args.interval_seconds, logger)
    finally:
        backend.release()
        logger.info("Camera released")


if __name__ == "__main__":
    raise SystemExit(main())
