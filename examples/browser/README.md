# نمونهٔ میکروفن · Microphone demo

این نمونه روی رایانهٔ خود توسعه‌دهنده اجرا می‌شود. کلید فقط در متغیر محیطی سرور پایتون است و به مرورگر فرستاده نمی‌شود. مدل لایو یا فیوژن را انتخاب کنید، دسترسی میکروفن بدهید و صحبت کنید.

Run this example on your own development computer. The key remains in the Python backend's environment; it is never sent to the browser. Choose Live or Fusion, allow microphone access, and speak.

از ریشهٔ مخزن / From the repository root

```bash
python -m pip install -r examples/browser/requirements.txt
# Set NEVISA_API_KEY and optionally NEVISA_BASE_URL in this shell first.
python -m uvicorn server:app --app-dir examples/browser --host 127.0.0.1 --port 8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Chrome/Edge with AudioWorklet and a 16 kHz AudioContext are suitable. Stop waits for the final result; capture automatically stops after one minute. Unsupported sample rates produce an error rather than mislabeled audio.

در محصول عمومی باید ورود و مجوز کاربر، کنترل مصرف، WSS، محدودیت هم‌زمانی و مدیریت نشست را در بک‌اند خودتان پیاده کنید. این سرور نمونه را با آدرس عمومی یا بدون احراز هویت منتشر نکنید. فهرست origin مجاز نمونه فقط localhost با پورت ۸۷۶۵ است.

For a deployed product, add your application's authentication and authorization, credit/concurrency controls, WSS and session lifecycle handling to the relay. Keep this demo bound to loopback; it has no multi-user login. Its origin allowlist only permits localhost on port 8765.
