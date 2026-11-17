# Verification · بررسی نمونه‌ها

On 2026-11-18, the runnable clients completed **18 real API checks** against the online Nevisa platform (API v1). Test recordings were synthesized for the checks, and the OCR document was generated for testing. No private customer recordings were used.

در ۱۸ نوامبر ۲۰۲۶، نمونه‌های اجرایی در **۱۸ آزمون واقعی API** پلتفرم آنلاین نویسا موفق بودند. صوت و سند مورد استفاده مخصوص آزمون تولید شدند. این بررسی صحت اتصال و تکمیل درخواست را می‌سنجد؛ ارزیابی جامع دقت تشخیص گفتار یا OCR نیست.

| Client | Verified requests |
|---|---|
| Python | Balance, discovery, Ariana Nova speaker 1, Ariana Ava speaker 3, Nevisa File/Live/Fusion file ASR, live WebSocket with and without fusion, Bina image and PDF, language model |
| Node.js | Balance, Ariana Nova speaker 2, fusion file ASR, Bina PDF, language model |
| Bash/cURL | File upload, polling and transcript |

The HTTP contract tests also check revoked keys, failed jobs, rejected uploads, speaker mapping, file downloads, and documentation links. Run them locally after installing the Python requirements and Node.js.

```bash
python -m pip install -r examples/python/requirements.txt -r examples/browser/requirements.txt httpx
python -m unittest discover -s tests -v
node tests/pcm-worklet.mjs
```

[Automated checks](https://github.com/persian-speech/nevisa-developers/actions/workflows/examples.yml) run without production credentials. Availability on another account or an enterprise installation must be checked with that installation's discovery endpoints.
