import argparse
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth import is_authorized
from app.input_control import INPUT_AVAILABLE, router as input_router
from app.screen_stream import router as stream_router

BASE_DIR = Path(__file__).parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Smart PC Remote Desktop (LAN)")
app.include_router(input_router)
app.include_router(stream_router)


@app.get("/controller", response_class=HTMLResponse)
def get_controller(request: Request, token: str | None = None):
    if not is_authorized(token):
        hint = (
            "Unauthorized (401): token が一致しません。"
            "\nURL の token パラメータと、PC 側で設定した CONTROL_TOKEN を同じ値にしてください。"
            "\n例: /controller?token=change-me"
        )
        return HTMLResponse(hint, status_code=401)

    return TEMPLATES.TemplateResponse(
        request,
        "controller.html",
        {
            "ws_path": f"/ws/control?token={token}",
            "stream_path": f"/stream.mjpeg?token={token}&fps=24&quality=45",
            "input_available": INPUT_AVAILABLE,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)
