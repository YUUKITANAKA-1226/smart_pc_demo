import argparse
import asyncio
import json
import os
import time
from dataclasses import dataclass

import av
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from fastapi import FastAPI, HTTPException
from mss import mss
from pydantic import BaseModel

try:
    from pynput.keyboard import Controller as KeyboardController, Key
    from pynput.mouse import Button, Controller as MouseController

    mouse = MouseController()
    keyboard = KeyboardController()
    INPUT_AVAILABLE = True
except Exception:
    mouse = None
    keyboard = None
    Key = None
    Button = None
    INPUT_AVAILABLE = False

APP = FastAPI(title="Native Remote Host")
PEER_CONNECTIONS: set[RTCPeerConnection] = set()
PAIR_CODE = os.getenv("PAIR_CODE", "123456")


class OfferRequest(BaseModel):
    pair_code: str
    sdp: str
    type: str


class OfferResponse(BaseModel):
    sdp: str
    type: str


class HealthResponse(BaseModel):
    ok: bool
    input_available: bool


@dataclass
class MonitorInfo:
    left: int
    top: int
    width: int
    height: int


class ScreenTrack(VideoStreamTrack):
    def __init__(self, fps: int = 30):
        super().__init__()
        self.fps = max(5, min(fps, 60))
        self.frame_time = 1.0 / self.fps
        self.last_frame_at = 0.0
        self.sct = mss()
        mon = self.sct.monitors[1]
        self.monitor = MonitorInfo(mon["left"], mon["top"], mon["width"], mon["height"])

    async def recv(self):
        now = time.perf_counter()
        delta = now - self.last_frame_at
        if delta < self.frame_time:
            await asyncio.sleep(self.frame_time - delta)
        self.last_frame_at = time.perf_counter()

        shot = self.sct.grab({
            "left": self.monitor.left,
            "top": self.monitor.top,
            "width": self.monitor.width,
            "height": self.monitor.height,
        })
        frame = np.frombuffer(shot.rgb, dtype=np.uint8).reshape((shot.height, shot.width, 3))
        video_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts, video_frame.time_base = await self.next_timestamp()
        return video_frame


def apply_input_event(payload: dict) -> None:
    if not INPUT_AVAILABLE:
        return

    event_type = payload.get("type")

    if event_type == "mouse_abs":
        x = int(payload.get("x", 0))
        y = int(payload.get("y", 0))
        mouse.position = (x, y)
        return

    if event_type == "mouse_click":
        mapping = {"left": Button.left, "right": Button.right, "middle": Button.middle}
        mouse.click(mapping.get(payload.get("button", "left"), Button.left), 1)
        return

    if event_type == "text":
        text = payload.get("text", "")
        if isinstance(text, str) and text:
            keyboard.type(text)
        return

    if event_type == "key":
        key_name = str(payload.get("key", "")).lower()
        special = {
            "enter": Key.enter,
            "backspace": Key.backspace,
            "tab": Key.tab,
            "esc": Key.esc,
            "space": Key.space,
        }
        target = special.get(key_name)
        if target is None and len(key_name) == 1:
            target = key_name
        if target is not None:
            keyboard.press(target)
            keyboard.release(target)


@APP.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True, input_available=INPUT_AVAILABLE)


@APP.post("/api/webrtc/offer", response_model=OfferResponse)
async def webrtc_offer(offer: OfferRequest) -> OfferResponse:
    if offer.pair_code != PAIR_CODE:
        raise HTTPException(status_code=401, detail="Invalid pair code")

    pc = RTCPeerConnection()
    PEER_CONNECTIONS.add(pc)

    @pc.on("datachannel")
    def on_datachannel(channel):
        if channel.label != "input":
            return

        @channel.on("message")
        def on_message(message):
            if isinstance(message, str):
                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:
                    return
                apply_input_event(payload)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState in {"failed", "closed", "disconnected"}:
            await pc.close()
            PEER_CONNECTIONS.discard(pc)

    pc.addTrack(ScreenTrack(fps=30))

    await pc.setRemoteDescription(RTCSessionDescription(sdp=offer.sdp, type=offer.type))
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return OfferResponse(sdp=pc.localDescription.sdp, type=pc.localDescription.type)


@APP.on_event("shutdown")
async def shutdown_event():
    await asyncio.gather(*[pc.close() for pc in list(PEER_CONNECTIONS)], return_exceptions=True)
    PEER_CONNECTIONS.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(APP, host=args.host, port=args.port)
