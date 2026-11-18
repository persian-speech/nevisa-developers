"""Runnable Nevisa REST / WebSocket examples. See --help and docs/en/README.md."""

import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
import wave

import requests


class Nevisa:
    def __init__(self):
        self.base = os.environ.get("NEVISA_BASE_URL", "https://persianspeech.com").rstrip("/")
        key = os.environ.get("NEVISA_API_KEY", "").strip()
        if not key:
            raise ValueError("Set NEVISA_API_KEY to your personal API key.")
        if not self.base.startswith(("https://", "http://")):
            raise ValueError("NEVISA_BASE_URL must be an HTTP(S) origin.")
        self.headers = {"X-API-Key": key}
        self.timeout = float(os.environ.get("NEVISA_TIMEOUT", "600"))
        self.session = requests.Session()

    def request(self, method, path, **kwargs):
        # Never follow redirects with a credential header to another origin.
        response = self.session.request(
            method, self.base + path, headers=self.headers,
            timeout=(15, min(180, self.timeout)), allow_redirects=False, **kwargs,
        )
        if not 200 <= response.status_code < 300:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:1000]}")
        return response

    def json(self, method, path, **kwargs):
        return self.request(method, path, **kwargs).json()

    def wait(self, service, job):
        path = {"asr": "/api/jobs/", "tts": "/api/tts/jobs/", "ocr": "/api/ocr/jobs/"}[service]
        deadline = time.monotonic() + self.timeout
        while job["status"] not in ("completed", "failed", "canceled"):
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Polling deadline reached. Resume with GET {path}{job['job_key']}/")
            time.sleep(2)
            job = self.json("GET", f"{path}{job['job_key']}/")
        if job["status"] != "completed":
            raise RuntimeError(job.get("error_message") or job["status"])
        return job

    @staticmethod
    def created(body, array=True):
        if body.get("errors"):
            raise RuntimeError(json.dumps(body["errors"], ensure_ascii=False))
        value = body.get("created")
        if not value:
            raise RuntimeError("No job was accepted.")
        return value[0] if array else value

    def asr(self, filename, engine):
        with open(filename, "rb") as audio:
            body = self.json("POST", "/api/jobs/upload/", files={"audio": audio},
                             data={"language": "fa", "engine": engine})
        return self.wait("asr", self.created(body))["result_text"]

    def tts(self, text, model, speaker, output):
        models = self.json("GET", "/api/tts/jobs/models/")
        selected = next(
            (item for item in models if item["id"] == model or item.get("pricing_key") == model),
            None,
        )
        if selected is None:
            raise ValueError("Model unavailable. Run discover and choose an offered TTS id.")
        voices = selected.get("voices") or []
        if speaker < 1 or speaker > len(voices):
            raise ValueError(f"Choose a speaker number between 1 and {len(voices)}.")
        # Send form encoding; this endpoint doesn't accept a JSON request body.
        body = self.json("POST", "/api/tts/jobs/synthesize/",
                         data={"text": text, "model": selected["id"], "voice": voices[speaker - 1], "language": "fa"})
        job = self.wait("tts", self.created(body, array=False))
        audio = self.request("GET", f"/api/tts/jobs/{job['job_key']}/audio/?format=mp3&download=1")
        Path(output).write_bytes(audio.content)
        return f"Saved {output} ({len(audio.content)} bytes)"

    def ocr(self, filename, pages):
        with open(filename, "rb") as document:
            body = self.json("POST", "/api/ocr/jobs/upload/", files={"document": document},
                             data={"engine": "bina", "language": "fa", "pages": pages})
        return self.wait("ocr", self.created(body))["result_text"]

    def chat(self, prompt):
        models = self.json("GET", "/api/llm/v1/models")["data"]
        if not models:
            raise ValueError("No language model is available for this account.")
        body = self.json("POST", "/api/llm/v1/chat/completions", json={
            "model": models[0]["id"], "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 128, "stream": False,
        })
        return body["choices"][0]["message"]["content"]

    def discover(self):
        result = {}
        for name, path in (
            ("asr", "/api/jobs/engines/"), ("tts", "/api/tts/jobs/models/"),
            ("ocr", "/api/ocr/jobs/engines/"), ("llm", "/api/llm/v1/models"),
        ):
            try:
                result[name] = self.json("GET", path)
            except (RuntimeError, requests.RequestException) as exc:
                result[name] = {"error": str(exc)}
        return json.dumps(result, ensure_ascii=False, indent=2)

    def live(self, filename, fusion):
        from websockets.sync.client import connect

        with wave.open(filename, "rb") as audio:
            if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 16000):
                raise ValueError("Use mono PCM16 WAV at 16000 Hz; see the ffmpeg command in the guide.")
            pcm = audio.readframes(audio.getnframes())
        url = self.base.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
        url += "/api/live/v1/stream"
        # The key is in a header, never in the URL or logs.
        with connect(url, additional_headers=self.headers, open_timeout=15, close_timeout=5) as ws:
            ws.send(json.dumps({"type": "start", "language": "fa", "sample_rate": 16000, "fusion": fusion}))
            started = json.loads(ws.recv(timeout=30))
            if started.get("type") != "started":
                raise RuntimeError(json.dumps(started, ensure_ascii=False))
            stop = threading.Event()
            send_error = []

            def send_audio():
                try:
                    for offset in range(0, len(pcm), 6400):
                        if stop.is_set():
                            return
                        ws.send(pcm[offset:offset + 6400])  # 200 ms PCM frames
                        stop.wait(0.2)  # microphone applications use actual capture timing
                    ws.send(json.dumps({"type": "stop"}))
                except Exception as exc:
                    send_error.append(exc)

            sender = threading.Thread(target=send_audio, daemon=True)
            sender.start()
            deadline = time.monotonic() + self.timeout
            finals = []
            try:
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("Live stream deadline reached.")
                    message = json.loads(ws.recv(timeout=min(60, remaining)))
                    kind = message.get("type")
                    if kind == "final":
                        finals.append(message.get("text", ""))
                    elif kind == "done":
                        return " ".join(finals)
                    elif kind in ("error", "usage_exhausted", "site_unavailable"):
                        raise RuntimeError(json.dumps(message, ensure_ascii=False))
                    if send_error:
                        raise send_error[0]
            finally:
                stop.set()
                sender.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("balance")
    sub.add_parser("discover")
    asr = sub.add_parser("asr")
    asr.add_argument("file")
    asr.add_argument("--engine", choices=["nevisa-file", "nevisa-live", "nevisa-fusion"], default="nevisa-file")
    tts = sub.add_parser("tts")
    tts.add_argument("text")
    tts.add_argument("--model", default="pocket-nova", help="Ariana Nova: pocket-nova; Ariana Ava: ariana-ava")
    tts.add_argument("--speaker", type=int, default=1)
    tts.add_argument("--output", default="speech.mp3")
    ocr = sub.add_parser("ocr")
    ocr.add_argument("file")
    ocr.add_argument("--pages", default="", help="PDF pages, 1-based, e.g. 1-3 or 1,4; blank means all")
    chat = sub.add_parser("chat")
    chat.add_argument("prompt")
    live = sub.add_parser("live")
    live.add_argument("file")
    live.add_argument("--fusion", action="store_true")
    args = parser.parse_args()
    client = Nevisa()
    try:
        if args.command == "balance":
            print(json.dumps(client.json("GET", "/api/billing/balance/"), ensure_ascii=False, indent=2))
        elif args.command == "discover":
            print(client.discover())
        elif args.command == "asr":
            print(client.asr(args.file, args.engine))
        elif args.command == "tts":
            print(client.tts(args.text, args.model, args.speaker, args.output))
        elif args.command == "ocr":
            print(client.ocr(args.file, args.pages))
        elif args.command == "chat":
            print(client.chat(args.prompt))
        elif args.command == "live":
            print(client.live(args.file, args.fusion))
    finally:
        client.session.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, TimeoutError, OSError, requests.RequestException) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
