import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .auth import is_authorized

router = APIRouter()

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

MONITOR = None
if INPUT_AVAILABLE:
    try:
        from mss import mss

        with mss() as sct:
            MONITOR = sct.monitors[1]
    except Exception:
        MONITOR = None


def _move_mouse_absolute(x_norm: float, y_norm: float) -> None:
    if MONITOR is None:
        return

    x_norm = max(0.0, min(1.0, x_norm))
    y_norm = max(0.0, min(1.0, y_norm))

    x = int(MONITOR["left"] + (MONITOR["width"] - 1) * x_norm)
    y = int(MONITOR["top"] + (MONITOR["height"] - 1) * y_norm)
    mouse.position = (x, y)


def handle_control_event(event: dict) -> None:
    if not INPUT_AVAILABLE:
        return

    event_type = event.get("type")

    if event_type == "mouse_abs":
        x_norm = float(event.get("x_norm", 0.0))
        y_norm = float(event.get("y_norm", 0.0))
        _move_mouse_absolute(x_norm, y_norm)
        return

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


@router.websocket("/ws/control")
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
