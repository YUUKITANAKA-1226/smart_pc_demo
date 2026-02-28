from io import BytesIO
import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from mss import mss
from PIL import Image, ImageDraw

from .auth import is_authorized

router = APIRouter()

BOUNDARY = "frame"


def _placeholder_frame() -> bytes:
    image = Image.new("RGB", (1280, 720), color=(20, 20, 20))
    draw = ImageDraw.Draw(image)
    draw.text((40, 40), "Screen capture unavailable in this environment", fill=(240, 240, 240))
    draw.text((40, 80), "Please run on a PC desktop session.", fill=(220, 220, 220))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=70)
    return buffer.getvalue()


def _jpeg_bytes() -> bytes:
    with mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        image = Image.frombytes("RGB", shot.size, shot.rgb)
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=60)
        return buffer.getvalue()


def _frame_generator(target_fps: int = 12):
    frame_delay = 1.0 / max(1, target_fps)
    while True:
        try:
            jpeg = _jpeg_bytes()
        except Exception:
            jpeg = _placeholder_frame()

        yield (
            f"--{BOUNDARY}\r\n"
            "Content-Type: image/jpeg\r\n"
            f"Content-Length: {len(jpeg)}\r\n\r\n"
        ).encode("utf-8") + jpeg + b"\r\n"
        time.sleep(frame_delay)


@router.get("/stream.mjpeg")
def stream_mjpeg(token: str | None = None, fps: int = 12):
    if not is_authorized(token):
        return StreamingResponse(iter([b"Unauthorized"]), status_code=401, media_type="text/plain")

    return StreamingResponse(
        _frame_generator(target_fps=min(max(fps, 1), 20)),
        media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}",
        headers={"Cache-Control": "no-store"},
    )
