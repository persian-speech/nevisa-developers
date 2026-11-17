"""Local microphone demo. Bind to 127.0.0.1; production needs your application's auth."""
import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from websockets.asyncio.client import connect

app = FastAPI()
HERE = Path(__file__).parent
ORIGINS = {"http://127.0.0.1:8765", "http://localhost:8765"}


@app.get("/")
async def index():
    return FileResponse(HERE / "index.html")


@app.get("/pcm-worklet.js")
async def worklet():
    return FileResponse(HERE / "pcm-worklet.js", media_type="text/javascript")


@app.websocket("/stream")
async def stream(client: WebSocket):
    # Local demo only. Origin check blocks cross-site use of the local API key.
    if client.headers.get("origin") not in ORIGINS:
        await client.close(code=1008)
        return
    key = os.environ.get("NEVISA_API_KEY", "").strip()
    if not key:
        await client.close(code=1011, reason="Set NEVISA_API_KEY on the demo server")
        return
    await client.accept()
    base = os.environ.get("NEVISA_BASE_URL", "https://persianspeech.com").rstrip("/")
    url = base.replace("https://", "wss://", 1).replace("http://", "ws://", 1) + "/api/live/v1/stream"
    tasks = []
    try:
        async with connect(url, additional_headers={"X-API-Key": key}, open_timeout=15, close_timeout=5) as upstream:
            async def send():
                while True:
                    message = await client.receive()
                    if message["type"] == "websocket.disconnect":
                        return
                    payload = message.get("bytes")
                    await upstream.send(payload if payload is not None else message["text"])

            async def receive():
                async for message in upstream:
                    await client.send_text(message)

            tasks = [asyncio.create_task(send()), asyncio.create_task(receive())]
            done, _ = await asyncio.wait(tasks, timeout=600, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
    except Exception:
        # Don't echo upstream credentials, URLs, or diagnostics to a browser.
        try:
            await client.send_json({"type": "error", "detail": "Connection unavailable. Check key, credit and service availability."})
        except RuntimeError:
            pass
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        try:
            await client.close()
        except RuntimeError:
            pass
