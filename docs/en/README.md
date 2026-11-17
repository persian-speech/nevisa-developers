# Nevisa API guide

[فارسی](../fa/README.md) · [Home](../../README.md)

## 1. Account, key and configuration

Sign in at [persianspeech.com](https://persianspeech.com), open [API keys](https://persianspeech.com/dashboard/account/api-keys), create a personal key, and copy it when shown. Use [Developers](https://persianspeech.com/dashboard/developers) for interactive requests, service references and current rates.

HTTP requests accept `X-API-Key: nv_...` or `Authorization: Bearer nv_...`. The key grants access as its owner. Keep it on your backend, outside source control and client bundles. Revoke it from API keys if exposed. WebSocket clients can send `X-API-Key` during the handshake. Browser WebSocket cannot set custom headers; use an authenticated backend relay for a distributed application.

The base URL is the **origin**, without `/api` appended. For an enterprise installation, set the origin of that installation; its enabled services, model choices and account policy may differ. Discovery and the installation's own API reference are authoritative.

PowerShell

```powershell
$env:NEVISA_BASE_URL = "https://persianspeech.com"
$env:NEVISA_API_KEY = "nv_YOUR_API_KEY"
$env:NEVISA_TIMEOUT = "600"
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r examples/python/requirements.txt
python examples/python/nevisa.py balance
python examples/python/nevisa.py discover
```

Bash

```bash
export NEVISA_BASE_URL=https://persianspeech.com
export NEVISA_API_KEY=nv_YOUR_API_KEY
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r examples/python/requirements.txt
python examples/python/nevisa.py discover
```

The examples read environment variables directly; copying `.env.example` to `.env` does **not** load it automatically. Python 3.10+ is required. The JavaScript examples require Node.js 22+ and no npm packages.

## 2. Discover services and models

| Method | Path | Response |
|---|---|---|
| GET | `/api/jobs/engines/` | Available ASR engines and active model information |
| GET | `/api/tts/jobs/models/` | Array of TTS models, voice ids and capabilities |
| GET | `/api/ocr/jobs/engines/` | Available OCR engines |
| GET | `/api/llm/v1/models` | OpenAI-shaped `data` array |
| GET | `/api/billing/balance/` | Account credit and current rates |

Use Nevisa File (`nevisa-file`), Nevisa Live (`nevisa-live`) or Nevisa Fusion (`nevisa-fusion`) for file ASR. Omit `live_model` to use the server's active live model. Do not pin a previous model version unless the installation requires it.

Ariana Nova uses API id `pocket-nova`; Ariana Ava uses `chatterbox-persian`. These are stable API identifiers, not display names. Select an offered id from discovery. Label the returned preset voices **Speaker 1**, **Speaker 2**, etc., and send the corresponding voice id; do not display the raw voice id as the product label. The Python and JavaScript CLIs accept a 1-based speaker number and perform this mapping.

## 3. File transcription and fusion

```bash
python examples/python/nevisa.py asr recording.mp3
python examples/python/nevisa.py asr recording.mp3 --engine nevisa-live
python examples/python/nevisa.py asr recording.mp3 --engine nevisa-fusion
node examples/javascript/nevisa.mjs asr recording.mp3 nevisa-fusion
bash examples/curl/asr.sh recording.mp3 nevisa-file
```

POST multipart form data to `/api/jobs/upload/` with `audio`, `language=fa` and `engine`. Repeat the `audio` field for batch uploads. Optional fields include `word_timestamps=true`, `diarization=true` and `convert_numbers=true` where enabled. Language options depend on the selected engine; these examples use Persian.

The response contains `created` **as an array** and `errors` per rejected file. Check both, even on HTTP success. Save each accepted `job_key` and poll `GET /api/jobs/{job_key}/` every few seconds. On `completed`, read `result_text` and `segments`. Treat `failed` and `canceled` as terminal failures; a `paused` job needs action or later resumption. Examples stop polling at the configured deadline. A polling timeout does not cancel a server job; retain its key to resume.

Download exports using `GET /api/jobs/{job_key}/export/?format=txt`; supported formats are listed in the installation's schema. Delete a test job with `DELETE /api/jobs/{job_key}/delete/` when finished.

Fusion combines the live and file models. It may increase processing time and is not guaranteed to improve every recording. It must be enabled by the administrator. Compare on representative recordings for your application.

## 4. Live audio and microphone

```bash
ffmpeg -i recording.mp3 -ac 1 -ar 16000 -c:a pcm_s16le voice.wav
python examples/python/nevisa.py live voice.wav
python examples/python/nevisa.py live voice.wav --fusion
```

Connect to `wss://persianspeech.com/api/live/v1/stream` with the key header. Send a JSON start frame

```json
{"type":"start","language":"fa","sample_rate":16000,"fusion":false}
```

Wait for `started`, send binary **mono signed 16-bit little-endian PCM**, then send `{"type":"stop"}`. Do not send a WAV header or encoded MP3 bytes. The sample sends 200 ms frames at real-time speed and receives messages concurrently. For a microphone, feed the same format from your capture layer; see the [microphone example](../../examples/browser/README.md).

Replace the displayed provisional text on each `partial`; append only `final` text. Wait for `done` before closing, including after stopping capture. Handle `error`, `usage_exhausted`, `site_unavailable` and unexpected disconnects. Use `fusion=true` for Persian live fusion when enabled; partials arrive from the live recognizer and final text can be refined by the file model.

## 5. Text to speech

```bash
python examples/python/nevisa.py tts "سلام، به نویسا خوش آمدید." --model pocket-nova --speaker 1 --output nova.mp3
python examples/python/nevisa.py tts "سلام، روز خوبی داشته باشید." --model chatterbox-persian --speaker 3 --output ava.mp3
node examples/javascript/nevisa.mjs tts "سلام، خوش آمدید." pocket-nova 1 speech.mp3
```

POST **form data**, not JSON, to `/api/tts/jobs/synthesize/` with `text`, `model`, `voice`, and optionally `language=fa`. The response contains `created` **as an object**, not an array. Poll `GET /api/tts/jobs/{job_key}/` until completed. Download with the same key using `GET /api/tts/jobs/{job_key}/audio/?format=mp3&download=1`. Check the HTTP status before saving bytes.

For voice cloning, use a model advertising `voice_cloning=true` and add a `reference` audio file to multipart form data. Use only recordings you have permission to use. Reference upload replaces the preset voice for that request. Format, text length and file limits are set by the installation.

## 6. Image and PDF OCR

```bash
python examples/python/nevisa.py ocr scan.png
python examples/python/nevisa.py ocr document.pdf --pages 1-3
node examples/javascript/nevisa.mjs ocr document.pdf 1,4
```

POST multipart form data to `/api/ocr/jobs/upload/` with `document`, `engine=bina` and `language=fa`. For PDFs, `pages` is 1-based, e.g. `1-3` or `1,4`; blank means all pages. The response uses `created` **as an array** and `errors`. Poll `GET /api/ocr/jobs/{job_key}/`; completed results include `result_text` and `pages`. Download text using `GET /api/ocr/jobs/{job_key}/export/?format=txt`. Display the model name as **Bina**.

## 7. Language model

```bash
python examples/python/nevisa.py chat "در یک جمله بگو یادگیری ماشین چیست."
node examples/javascript/nevisa.mjs chat "در یک جمله بگو یادگیری ماشین چیست."
```

POST JSON to `/api/llm/v1/chat/completions`. Send `messages` with roles `system`, `user`, `assistant`, optional `max_tokens` and `temperature`. The administrator selects the serving model; discovery returns the model available to your account. Setting an arbitrary `model` does not switch the server's backend. OpenAI-compatible clients can use base URL `https://persianspeech.com/api/llm/v1` and your Nevisa API key.

```json
{"messages":[{"role":"user","content":"سلام"}],"max_tokens":128,"stream":false}
```

Read `choices[0].message.content` from a non-streaming response. With `stream=true`, read SSE `data:` events, append `choices[].delta.content`, handle an `error` event, and stop at `[DONE]`. The runnable CLIs use non-streaming requests.

## 8. Credit, errors and integration behavior

All requests use the same account. ASR/live usage is based on audio duration and the model rate; TTS uses generated audio duration; OCR uses page count; LLM uses tokens. See current rates and balances in the developer reference rather than hard-coding prices. Subscription, daily allowance and enterprise policy can affect eligibility.

| HTTP / event | What to do |
|---|---|
| 400 / validation, `duration_limit` | Correct fields, file format or length; inspect `errors` for batch jobs |
| 401 | Check or revoke/recreate the key |
| 402 / `insufficient_credit`, 400 / `usage_exceeded` | Check balance and account eligibility |
| 403 / `section_disabled` | Service disabled by the administrator |
| 429 | Respect `Retry-After` when present; reduce concurrency |
| 503 / `maintenance`, `billing_unavailable` | Retry safe reads with backoff after availability returns |
| WS `usage_exhausted` | Stop capture and check credit |
| Job `failed`, `canceled` | Surface the error, retain job key for support |

POST submissions are not documented as idempotent. Do not retry uploads or synthesis automatically after an ambiguous network timeout; check your job list first to avoid duplicate processing and charges. Poll with a deadline and backoff; do not hammer the queue. Never put API keys in public frontend bundles, URLs in logs, screenshots or issue reports.

## 9. Live API reference and support

Open the installation's schemas for deployment-specific limits

- [ASR](https://persianspeech.com/api/asr/schema/swagger-ui/)
- [TTS](https://persianspeech.com/api/tts/schema/swagger-ui/)
- [OCR](https://persianspeech.com/api/ocr/schema/swagger-ui/)
- [LLM](https://persianspeech.com/api/llm/schema/swagger-ui/)
- [Account and billing](https://persianspeech.com/api/schema/swagger-ui/)

For sample-code problems, [open an issue](https://github.com/persian-speech/nevisa-developers/issues). Include the language/runtime version, HTTP status, endpoint and a redacted minimal reproduction. Account and private-file problems belong in the platform's support section.
