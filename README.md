# نویسا برای توسعه‌دهندگان · Nevisa for developers

[راهنمای فارسی](docs/fa/README.md) · [English guide](docs/en/README.md) · [پلتفرم نویسا / Platform](https://persianspeech.com) · [API keys](https://persianspeech.com/dashboard/account/api-keys) · [Playground](https://persianspeech.com/dashboard/developers)

API تبدیل گفتار به متن، گفتار زنده و فیوژن، تبدیل متن به گفتار، OCR تصویر و PDF و مدل زبانی نویسا، همراه نمونه‌های قابل اجرا.

Integrate Nevisa speech recognition, live streaming and fusion, speech synthesis, image/PDF OCR, and language models.

| سرویس / Service | نام محصول / Product | نمونه / Example |
|---|---|---|
| ASR فایل / File ASR | نویسا فایل / Nevisa File | `python examples/python/nevisa.py asr audio.mp3` |
| ASR لایو / Live ASR | نویسا لایو / Nevisa Live | `python examples/python/nevisa.py live voice.wav` |
| ASR فیوژن / Fusion ASR | نویسا فیوژن / Nevisa Fusion | `python examples/python/nevisa.py asr audio.mp3 --engine nevisa-fusion` |
| TTS | آریانا نوا، آریانا آوا، آریانا ندا / Ariana Nava, Ariana Ava, Ariana Neda | `python examples/python/nevisa.py tts "سلام، خوش آمدید."` |
| OCR | Bina | `python examples/python/nevisa.py ocr scan.pdf --pages 1` |
| LLM | مدل زبانی نویسا / Nevisa language model | `python examples/python/nevisa.py chat "یک جمله درباره بهار بنویس."` |

ابتدا کلید API را در متغیر محیطی تنظیم کنید. دسترسی سرویس‌ها و مصرف اعتبار به تنظیمات سرور و حساب شما بستگی دارد.
Set your API key in the environment first. Service availability and credit usage depend on your server and account.

## Examples

[بررسی نمونه‌ها / Verification](docs/VALIDATION.md)

- [Python CLI](examples/python/nevisa.py) — REST and WebSocket, Python 3.10+.
- [JavaScript CLI](examples/javascript/nevisa.mjs) — REST, Node.js 22+, no npm dependencies.
- [cURL ASR workflow](examples/curl/asr.sh) — Bash, curl and jq, including polling.
- [Browser microphone example](examples/browser/README.md) — capture and stream through a backend that holds the key.

این مخزن کد سرور یا مدل‌ها را توزیع نمی‌کند. مشکلات مربوط به مستندات و نمونه‌ها را در [Issues](https://github.com/persian-speech/nevisa-developers/issues) مطرح کنید. کلید، فایل محرمانه یا اطلاعات حساب را در issue قرار ندهید.

This repository contains integration documentation and examples. Report documentation/example problems in [Issues](https://github.com/persian-speech/nevisa-developers/issues); keep API keys, private recordings and account details out of public reports.
