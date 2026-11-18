"""Run both clients against an HTTP contract fixture, including error responses."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]


class API(BaseHTTPRequestHandler):
    mode = "ok"
    calls = []

    def log_message(self, *args):
        pass

    def reply(self, body, code=200, content_type="application/json"):
        data = json.dumps(body).encode() if content_type == "application/json" else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.headers.get("X-API-Key") != "nv_contract_fixture":
            return self.reply({"detail": "Invalid key"}, 401)
        if API.mode == "unauthorized":
            return self.reply({"detail": "Revoked key"}, 401)
        if self.path.endswith("audio/?format=mp3&download=1"):
            return self.reply(b"ID3-fixture", content_type="audio/mpeg")
        if self.path == "/api/tts/jobs/models/":
            return self.reply([{"id": "pocket-nova", "voices": ["speaker-1", "speaker-2", "speaker-3"]}])
        if self.path == "/api/ocr/jobs/engines/":
            return self.reply([{"id": "bina", "label": "Bina"}])
        if self.path == "/api/jobs/engines/":
            return self.reply({"engines": [{"id": "nevisa-file"}, {"id": "nevisa-fusion"}]})
        if self.path == "/api/llm/v1/models":
            return self.reply({"data": [{"id": "nevisa-llm"}]})
        if self.path == "/api/billing/balance/":
            return self.reply({"remaining_seconds": 600, "rates": {"nevisa-file": 1}})
        status = "failed" if API.mode == "failed" else "completed"
        return self.reply({"job_key": "fixture-job", "status": status, "result_text": "متن آزمایشی", "error_message": "fixture failure" if status == "failed" else ""})

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        API.calls.append((self.path, body, self.headers.get("Content-Type", "")))
        if self.path == "/api/llm/v1/chat/completions":
            data = json.loads(body)
            assert data["model"] == "nevisa-llm"
            return self.reply({"choices": [{"message": {"content": "پاسخ آزمایشی"}}]})
        if API.mode == "partial":
            return self.reply({"created": [], "errors": [{"code": "duration_limit"}]}, 201)
        job = {"job_key": "fixture-job", "status": "queued"}
        self.reply({"created": job} if "/tts/" in self.path else {"created": [job], "errors": []}, 201)


class Examples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), API)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.directory = tempfile.TemporaryDirectory()
        cls.fixture = Path(cls.directory.name) / "fixture.wav"
        cls.fixture.write_bytes(b"fixture")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.directory.cleanup()

    def clients(self):
        yield [sys.executable, str(ROOT / "examples/python/nevisa.py")], "python"
        node = os.environ.get("NEVISA_TEST_NODE") or shutil.which("node")
        if node:
            yield [node, str(ROOT / "examples/javascript/nevisa.mjs")], "javascript"

    def run_cli(self, command, args, mode="ok"):
        API.mode = mode
        env = dict(os.environ, NEVISA_API_KEY="nv_contract_fixture", NEVISA_BASE_URL=f"http://127.0.0.1:{self.server.server_port}", NEVISA_TIMEOUT="10", PYTHONIOENCODING="utf-8")
        return subprocess.run(command + args, env=env, capture_output=True, text=True, encoding="utf-8", timeout=20)

    def test_all_rest_workflows(self):
        for command, language in self.clients():
            output = str(Path(self.directory.name) / f"{language}.mp3")
            cases = [(["balance"], "remaining_seconds"), (["discover"], "pocket-nova"),
                     (["asr", str(self.fixture)] + (["--engine", "nevisa-fusion"] if language == "python" else ["nevisa-fusion"]), "متن آزمایشی"),
                     (["ocr", str(self.fixture)] + (["--pages", "1,3"] if language == "python" else ["1,3"]), "متن آزمایشی"),
                     (["chat", "سلام"], "پاسخ آزمایشی"),
                     (["tts", "سلام"] + (["--speaker", "3", "--output", output] if language == "python" else ["pocket-nova", "3", output]), "Saved")]
            for args, expected in cases:
                with self.subTest(language=language, command=args[0]):
                    result = self.run_cli(command, args)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(expected, result.stdout)
            self.assertEqual(Path(output).read_bytes(), b"ID3-fixture")
        for path, body, content_type in API.calls:
            if path.endswith("synthesize/"):
                self.assertNotIn("application/json", content_type)
                self.assertTrue(b"speaker-3" in body)
            if path.endswith("/upload/") and "/ocr/" not in path:
                self.assertIn(b"nevisa-fusion", body)
                self.assertNotIn(b"live_model", body)

    def test_rejected_upload_and_revoked_key_fail(self):
        for command, language in self.clients():
            for args, mode, expected in [(["balance"], "unauthorized", "401"), (["asr", str(self.fixture)], "partial", "duration_limit"), (["asr", str(self.fixture)], "failed", "fixture failure")]:
                with self.subTest(language=language, mode=mode):
                    result = self.run_cli(command, args, mode)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected, result.stderr)

    def test_relative_document_links_resolve(self):
        import re
        for path in ROOT.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text("utf-8")):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((path.parent / target.split("#")[0]).exists(), (path, target))

    @unittest.skipUnless(all(shutil.which(tool) for tool in ("bash", "curl", "jq")), "Requires Bash, curl and jq")
    def test_curl_transcribes_and_polls(self):
        command = ["bash", str(ROOT / "examples/curl/asr.sh")]
        result = self.run_cli(command, [str(self.fixture), "nevisa-fusion"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("متن آزمایشی", result.stdout)


if __name__ == "__main__":
    unittest.main()
