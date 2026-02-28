import argparse
import json
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Button, Controller as MouseController

BASE_DIR = Path(__file__).parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Smart PC Control Receiver")
mouse = MouseController()
keyboard = KeyboardController()
CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "change-me")


def is_authorized(token: str | None) -> bool:
    return bool(token) and token == CONTROL_TOKEN


def handle_control_event(event: dict) -> None:
    event_type = event.get("type")

    if event_type == "mouse_move":
        dx = int(event.get("dx", 0))
        dy = int(event.get("dy", 0))
        x, y = mouse.position
        mouse.position = (x + dx, y + dy)
        return

    if event_type == "mouse_click":
        button_map = {
            "left": Button.left,
            "right": Button.right,
            "middle": Button.middle,
        }
        button = button_map.get(event.get("button", "left"), Button.left)
        mouse.click(button, 1)
        return

    if event_type == "key":
        key_name = event.get("key")
        special = {
            "enter": Key.enter,
            "backspace": Key.backspace,
            "tab": Key.tab,
            "esc": Key.esc,
            "space": Key.space,
        }
        key_to_press = special.get(str(key_name).lower()) if key_name else None
        if key_to_press is None and isinstance(key_name, str) and len(key_name) == 1:
            key_to_press = key_name
        if key_to_press is not None:
            keyboard.press(key_to_press)
            keyboard.release(key_to_press)
        return

    if event_type == "text":
        text = event.get("text", "")
        if isinstance(text, str) and text:
            keyboard.type(text)
        return


@app.get("/controller", response_class=HTMLResponse)
def get_controller(request: Request, token: str | None = None):
    if not is_authorized(token):
        return HTMLResponse("Unauthorized: invalid token", status_code=401)

    return TEMPLATES.TemplateResponse(
        request,
        "controller.html",
        {
            "ws_path": f"/ws/control?token={token}",
        },
    )


@app.websocket("/ws/control")
async def control_ws(websocket: WebSocket, token: str | None = None):
    if not is_authorized(token):
        await websocket.close(code=4401)
        return

    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            handle_control_event(event)
    except WebSocketDisconnect:
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)
