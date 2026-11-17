import asyncio
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('microphone_server', ROOT / 'examples/browser/server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class Upstream:
    def __init__(self):
        self.incoming = asyncio.Queue()
        self.frames = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def send(self, frame):
        self.frames.append(frame)
        if isinstance(frame, str) and 'start' in frame:
            await self.incoming.put('{"type":"started"}')
        if isinstance(frame, str) and 'stop' in frame:
            await self.incoming.put('{"type":"final","text":"fixture"}')
            await self.incoming.put('{"type":"done"}')
            await self.incoming.put(None)

    def __aiter__(self):
        return self

    async def __anext__(self):
        frame = await self.incoming.get()
        if frame is None:
            raise StopAsyncIteration
        return frame


class Microphone(unittest.TestCase):
    def test_local_relay_keeps_key_on_server_and_forwards_pcm(self):
        upstream = Upstream()
        with patch.dict(os.environ, {'NEVISA_API_KEY':'nv_local_fixture'}), patch.object(server, 'connect', return_value=upstream) as connect:
            with TestClient(server.app) as client:
                self.assertNotIn('nv_local_fixture', client.get('/').text)
                with client.websocket_connect('/stream', headers={'origin':'http://127.0.0.1:8765'}) as ws:
                    ws.send_text('{"type":"start","fusion":true}')
                    self.assertEqual(ws.receive_json()['type'], 'started')
                    ws.send_bytes(b'\x00\x01\x02\x03')
                    ws.send_text('{"type":"stop"}')
                    self.assertEqual(ws.receive_json()['text'], 'fixture')
                    self.assertEqual(ws.receive_json()['type'], 'done')
            self.assertIn(b'\x00\x01\x02\x03', upstream.frames)
            self.assertEqual(connect.call_args.kwargs['additional_headers'], {'X-API-Key':'nv_local_fixture'})
            self.assertNotIn('nv_local_fixture', connect.call_args.args[0])

    def test_cross_site_origin_cannot_use_local_key(self):
        from starlette.websockets import WebSocketDisconnect
        with TestClient(server.app) as client:
            with self.assertRaises(WebSocketDisconnect) as error:
                with client.websocket_connect('/stream', headers={'origin':'https://untrusted.example'}):
                    pass
            self.assertEqual(error.exception.code, 1008)


if __name__ == '__main__':
    unittest.main()
