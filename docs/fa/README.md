# راهنمای API نویسا

[English](../en/README.md) · [صفحهٔ اصلی](../../README.md)

## ۱. حساب، کلید و تنظیمات

در [پلتفرم نویسا](https://persianspeech.com) وارد شوید و از [مدیریت کلیدهای API](https://persianspeech.com/dashboard/account/api-keys) یک کلید شخصی بسازید. کلید را همان زمان نمایش کپی کنید. در [بخش توسعه‌دهندگان](https://persianspeech.com/dashboard/developers) می‌توانید درخواست آزمایشی بفرستید و نرخ‌ها و مرجع سرویس‌ها را ببینید.

در درخواست HTTP از هدر `X-API-Key: nv_...` یا `Authorization: Bearer nv_...` استفاده کنید. کلید اختیارات حساب صاحب آن را دارد؛ آن را فقط در بک‌اند نگه دارید و وارد کد عمومی، بستهٔ مرورگر یا گیت نکنید. کلید افشاشده را از پنل لغو کنید. در اتصال WebSocket هم می‌توان هدر `X-API-Key` فرستاد. مرورگر امکان تعیین هدر دلخواه WebSocket ندارد؛ برای برنامهٔ توزیع‌شده از واسط بک‌اند با احراز هویت کاربر استفاده کنید.

آدرس پایه همان آدرس اصلی سرور است، بدون افزودن `/api`. در نسخهٔ سازمانی آدرس سرور همان نصب را قرار دهید. سرویس‌های فعال، مدل‌ها و سیاست حساب در هر نصب ممکن است متفاوت باشند؛ پاسخ کشف مدل‌ها و مرجع API همان نصب ملاک هستند.

در PowerShell

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

در Bash

```bash
export NEVISA_BASE_URL=https://persianspeech.com
export NEVISA_API_KEY=nv_YOUR_API_KEY
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r examples/python/requirements.txt
python examples/python/nevisa.py discover
```

نمونه‌ها متغیرهای محیطی را مستقیم می‌خوانند؛ کپی کردن `.env.example` به `.env` به‌تنهایی آن‌ها را بارگذاری نمی‌کند. برای نمونهٔ پایتون نسخهٔ ۳.۱۰ به بالا و برای جاوااسکریپت Node.js نسخهٔ ۲۲ به بالا لازم است. نمونهٔ جاوااسکریپت وابستگی npm ندارد.

## ۲. دریافت سرویس‌ها و مدل‌های فعال

| روش | مسیر | نتیجه |
|---|---|---|
| GET | `/api/jobs/engines/` | موتورهای ASR و اطلاعات مدل فعال |
| GET | `/api/tts/jobs/models/` | آرایهٔ مدل‌های TTS، صداها و قابلیت‌ها |
| GET | `/api/ocr/jobs/engines/` | موتورهای OCR |
| GET | `/api/llm/v1/models` | آرایهٔ `data` با ساختار سازگار با OpenAI |
| GET | `/api/billing/balance/` | اعتبار حساب و نرخ‌ها |

برای تبدیل فایل از نویسا فایل با شناسهٔ `nevisa-file`، نویسا لایو با `nevisa-live` یا نویسا فیوژن با `nevisa-fusion` استفاده کنید. پارامتر `live_model` را نفرستید تا مدل فعال سرور انتخاب شود؛ نسخهٔ قدیمی را در کد ثابت نکنید.

شناسهٔ API آریانا نوا `pocket-nova` و آریانا آوا `ariana-ava` است. این‌ها شناسهٔ فنی درخواست هستند؛ نام نمایشی همان آریانا نوا و آریانا آوا باشد. فقط مدلی را انتخاب کنید که در پاسخ کشف مدل‌ها وجود دارد. صداهای پیش‌فرض را به‌ترتیب **گوینده ۱**، **گوینده ۲** و ... نمایش دهید و شناسهٔ متناظر را در درخواست بفرستید. نمونه‌های پایتون و جاوااسکریپت شمارهٔ گوینده را از ۱ می‌گیرند و این تطبیق را انجام می‌دهند.

## ۳. تبدیل فایل صوتی و فیوژن

```bash
python examples/python/nevisa.py asr recording.mp3
python examples/python/nevisa.py asr recording.mp3 --engine nevisa-live
python examples/python/nevisa.py asr recording.mp3 --engine nevisa-fusion
node examples/javascript/nevisa.mjs asr recording.mp3 nevisa-fusion
bash examples/curl/asr.sh recording.mp3 nevisa-file
```

فایل را با فرم multipart به `POST /api/jobs/upload/` بفرستید. فیلدها `audio`، `language=fa` و `engine` هستند. برای چند فایل، فیلد `audio` را تکرار کنید. گزینه‌های `word_timestamps=true`، `diarization=true` و `convert_numbers=true` در صورت فعال بودن قابل استفاده‌اند. زبان‌های پشتیبانی‌شده به موتور بستگی دارند؛ نمونه‌ها فارسی هستند.

پاسخ شامل `created` به شکل **آرایه** و `errors` برای فایل‌های ردشده است؛ حتی در پاسخ HTTP موفق هر دو را بررسی کنید. مقدار `job_key` هر کار پذیرفته‌شده را نگه دارید و وضعیت را هر چند ثانیه از `GET /api/jobs/{job_key}/` بگیرید. پس از `completed` متن در `result_text` و قطعات در `segments` قرار دارند. وضعیت‌های `failed` و `canceled` پایان ناموفق هستند؛ کار `paused` نیاز به اقدام یا ادامه در زمان دیگر دارد. نمونه‌ها پس از مهلت تعیین‌شده انتظار را متوقف می‌کنند. پایان مهلت انتظار، کار سرور را لغو نمی‌کند؛ با کلید همان کار می‌توانید وضعیت را دوباره بگیرید.

برای خروجی متن از `GET /api/jobs/{job_key}/export/?format=txt` استفاده کنید. قالب‌های دیگر در مرجع همان نصب آمده‌اند. کار آزمایشی را پس از استفاده با `DELETE /api/jobs/{job_key}/delete/` حذف کنید.

فیوژن خروجی دو مدل لایو و فایل را ترکیب می‌کند؛ ممکن است زمان بیشتری بگیرد و تضمینی برای بهتر بودن روی همهٔ فایل‌ها ندارد. مدیر باید آن را فعال کرده باشد. برای انتخاب مدل، نمونه‌های واقعی کاربرد خود را مقایسه کنید.

## ۴. تبدیل زنده و میکروفن

```bash
ffmpeg -i recording.mp3 -ac 1 -ar 16000 -c:a pcm_s16le voice.wav
python examples/python/nevisa.py live voice.wav
python examples/python/nevisa.py live voice.wav --fusion
```

به `wss://persianspeech.com/api/live/v1/stream` با هدر کلید متصل شوید و ابتدا پیام JSON زیر را بفرستید.

```json
{"type":"start","language":"fa","sample_rate":16000,"fusion":false}
```

منتظر `started` بمانید، سپس قطعات باینری **PCM تک‌کانالهٔ ۱۶ بیت علامت‌دار little-endian** را بفرستید. پایان ارسال با `{"type":"stop"}` اعلام می‌شود. هدر WAV یا بایت‌های MP3 را به‌جای PCM نفرستید. نمونهٔ اجرایی قطعات ۲۰۰ میلی‌ثانیه‌ای را با سرعت واقعی می‌فرستد و هم‌زمان پیام‌ها را دریافت می‌کند. برای ورودی میکروفن، همین قالب را از لایهٔ ضبط دریافت کنید؛ [نمونهٔ میکروفن](../../examples/browser/README.md) را ببینید.

پیام `partial` جای متن موقت قبلی را می‌گیرد و فقط متن `final` به خروجی نهایی اضافه می‌شود. پس از توقف ضبط، دریافت را تا `done` ادامه دهید. رویدادهای `error`، `usage_exhausted` و `site_unavailable` و قطع غیرمنتظره را مدیریت کنید. برای فیوژن زندهٔ فارسی، در صورت فعال بودن `fusion=true` بفرستید؛ متن موقت از مدل لایو می‌آید و متن نهایی می‌تواند با مدل فایل اصلاح شود.

## ۵. تبدیل متن به گفتار

```bash
python examples/python/nevisa.py tts "سلام، به نویسا خوش آمدید." --model pocket-nova --speaker 1 --output nava.mp3
python examples/python/nevisa.py tts "سلام، روز خوبی داشته باشید." --model ariana-ava --speaker 3 --output ava.mp3
node examples/javascript/nevisa.mjs tts "سلام، خوش آمدید." pocket-nova 1 speech.mp3
```

به `POST /api/tts/jobs/synthesize/` **فرم** بفرستید؛ بدنهٔ JSON پذیرفته نمی‌شود. فیلدها `text`، `model`، `voice` و در صورت نیاز `language=fa` هستند. پاسخ `created` این سرویس **یک شیء** است، نه آرایه. از `GET /api/tts/jobs/{job_key}/` وضعیت را بگیرید و پس از تکمیل، صوت را با همان کلید از `GET /api/tts/jobs/{job_key}/audio/?format=mp3&download=1` دانلود کنید. پیش از ذخیرهٔ بایت‌ها وضعیت HTTP را بررسی کنید.

برای شبیه‌سازی صدای مجاز خود، مدلی را انتخاب کنید که `voice_cloning=true` دارد و فایل صوتی `reference` را در فرم multipart بفرستید. در این درخواست نمونهٔ صوت جای گویندهٔ پیش‌فرض را می‌گیرد. محدودیت متن، قالب و اندازهٔ فایل را از مرجع نصب ببینید.

## ۶. OCR تصویر و PDF

```bash
python examples/python/nevisa.py ocr scan.png
python examples/python/nevisa.py ocr document.pdf --pages 1-3
node examples/javascript/nevisa.mjs ocr document.pdf 1,4
```

فایل را با فیلد `document` و گزینه‌های `engine=bina` و `language=fa` به `POST /api/ocr/jobs/upload/` بفرستید. برای PDF، فیلد `pages` شماره‌گذاری از ۱ دارد؛ مثلاً `1-3` یا `1,4`. مقدار خالی یعنی همهٔ صفحات. پاسخ شامل آرایهٔ `created` و `errors` است. وضعیت را از `GET /api/ocr/jobs/{job_key}/` بگیرید؛ متن کامل در `result_text` و نتیجهٔ صفحات در `pages` قرار دارد. دریافت متن از `GET /api/ocr/jobs/{job_key}/export/?format=txt` انجام می‌شود. نام نمایشی مدل را فقط **Bina** بنویسید.

## ۷. مدل زبانی

```bash
python examples/python/nevisa.py chat "در یک جمله بگو یادگیری ماشین چیست."
node examples/javascript/nevisa.mjs chat "در یک جمله بگو یادگیری ماشین چیست."
```

به `POST /api/llm/v1/chat/completions` بدنهٔ JSON بفرستید. آرایهٔ `messages` شامل نقش‌های `system`، `user` و `assistant` است. گزینه‌های `max_tokens` و `temperature` اختیاری هستند. مدیر مدل سرویس‌دهنده را انتخاب می‌کند و مسیر کشف مدل، گزینهٔ در دسترس حساب شما را نشان می‌دهد؛ ارسال یک نام دلخواه در `model` مدل پشت سرویس را تغییر نمی‌دهد. کتابخانه‌های سازگار با OpenAI می‌توانند از آدرس پایهٔ `https://persianspeech.com/api/llm/v1` و کلید نویسا استفاده کنند.

```json
{"messages":[{"role":"user","content":"سلام"}],"max_tokens":128,"stream":false}
```

در پاسخ معمولی متن را از `choices[0].message.content` بخوانید. با `stream=true` رویدادهای SSE با پیشوند `data:` دریافت می‌شوند؛ `choices[].delta.content` را به متن اضافه کنید، پیام `error` را مدیریت کنید و با `[DONE]` دریافت را تمام کنید. نمونه‌های اجرایی از پاسخ معمولی استفاده می‌کنند.

## ۸. اعتبار و مدیریت خطا

همهٔ سرویس‌ها با حساب یکسان استفاده می‌شوند. مصرف ASR و لایو به زمان صوت و نرخ مدل، TTS به مدت صوت تولیدشده، OCR به تعداد صفحه و مدل زبانی به توکن وابسته است. نرخ و موجودی فعلی را از مرجع توسعه‌دهندگان بگیرید و قیمت را در کد ثابت نکنید. اشتراک، سهمیهٔ روزانه و سیاست نسخهٔ سازمانی بر امکان استفاده اثر دارند.

| HTTP یا رویداد | اقدام |
|---|---|
| 400، خطای اعتبارسنجی یا `duration_limit` | اصلاح فیلدها، قالب یا طول فایل؛ بررسی `errors` در ارسال گروهی |
| 401 | بررسی کلید و در صورت نیاز لغو و ساخت مجدد |
| 402 یا `insufficient_credit`، 400 یا `usage_exceeded` | بررسی موجودی و شرایط حساب |
| 403 یا `section_disabled` | سرویس از سوی مدیر غیرفعال شده است |
| 429 | رعایت `Retry-After` در صورت وجود و کاهش هم‌زمانی |
| 503 یا `maintenance`، `billing_unavailable` | تلاش با فاصله برای خواندن وضعیت پس از رفع اختلال |
| WS `usage_exhausted` | توقف ضبط و بررسی اعتبار |
| کار `failed` یا `canceled` | نمایش خطا و نگهداری کلید کار برای پشتیبانی |

برای درخواست POST تضمین idempotency مستند نشده است. پس از timeout مبهم، آپلود یا تولید صوت را خودکار تکرار نکنید؛ ابتدا فهرست کارها را بررسی کنید تا پردازش و هزینهٔ تکراری ایجاد نشود. دریافت وضعیت مهلت و فاصلهٔ مناسب داشته باشد. کلید را در بستهٔ عمومی مرورگر، آدرس ثبت‌شده در لاگ، تصویر صفحه یا issue منتشر نکنید.

## ۹. مرجع و پشتیبانی

محدودیت‌های همان استقرار را در مرجع زنده ببینید.

- [ASR](https://persianspeech.com/api/asr/schema/swagger-ui/)
- [TTS](https://persianspeech.com/api/tts/schema/swagger-ui/)
- [OCR](https://persianspeech.com/api/ocr/schema/swagger-ui/)
- [مدل زبانی](https://persianspeech.com/api/llm/schema/swagger-ui/)
- [حساب و اعتبار](https://persianspeech.com/api/schema/swagger-ui/)

برای اشکال راهنما یا نمونه‌ها [issue عمومی](https://github.com/persian-speech/nevisa-developers/issues) بسازید و نسخهٔ زبان، وضعیت HTTP، مسیر و نمونهٔ حداقلی بدون اطلاعات محرمانه را بنویسید. موضوعات حساب و فایل خصوصی را در پشتیبانی داخل پلتفرم مطرح کنید.
