# یادداشت‌های بررسی عمیق پروژه (Back/Front) – TowerCells RD

این فایل خلاصه‌ی معماری، جریان داده‌ها، مشکلات/ریسک‌ها و پیشنهادهای بهبود پروژه را ثبت می‌کند تا بعداً به عنوان «حافظه‌ی پروژه» به آن رجوع شود.

---

## 1) تصویر کلی (High-Level)

### هدف محصول
موقعیت‌یابی کاربر بر اساس داده‌ی سلولی (Cell Towers) با تکیه بر:
- دیتابیس محلی دکل‌ها (`CellTower`)
- در صورت نیاز، تکمیل داده با سرویس‌های خارجی (Combain / Google Geolocation)
- الگوریتم‌های تقریبی فاصله (Path Loss / TA) و تخمین نقطه (1/2/3+ tower)

### اجزا
- **Back-end:** Django + DRF (پروژه: `towercell`، اپ: `cellular`)
- **Front-end:** React + Vite + React-Leaflet (پوشه `front/`)
- **DB:** پیش‌فرض SQLite؛ قابل تغییر به PostgreSQL با `DJANGO_DB_BACKEND=postgres`
- **ابزارها:** Import CSV، Snapshot Locate، Swagger/OpenAPI

---

## 2) خلاصه بک‌اند (Backend Summary)

### تکنولوژی/ساختار
- Django + DRF + drf-spectacular برای OpenAPI:
  - `towercell/settings.py`
  - `towercell/urls.py`
  - `cellular/views.py`, `cellular/serializers.py`, `cellular/models.py`

### مدل‌های اصلی
- `CellTower` در `cellular/models.py`
  - شناسه‌ها: `mcc`, `mnc`, `lac` (اختیاری), `cell_id` (اختیاری اما عملاً باید کلیدی باشد)
  - موقعیت: `lat`, `lon`
  - سیگنال/رادیو: `radio_type`, `pci`, `earfcn`, `tx_power`, `antenna_azimuth`
  - متادیتا: `source`, `samples`, `checked_count`, `verified_count`, `is_approximate`
- `TowerLookupLog` برای لاگ درخواست‌های سرویس‌های خارجی

### سرویس‌ها و الگوریتم
- **هسته‌ی locate:** `cellular/services/locator.py:locate_cells`
  - `clean_cells` → `TowerResolver.resolve` → تخمین موقعیت
  - حالت‌ها:
    - **۱ دکل:** اگر TA موجود باشد از `distance_from_ta` + bearing استفاده می‌شود؛ در غیر این صورت Path Loss
    - **۲ دکل:** `trilaterate_two_towers` و fallback به `weighted_centroid`
    - **۳+ دکل:** انتخاب Top-3 بر اساس RSRP و `trilaterate_three` (NLLS + fallback)
- **رزولوشن دکل (DB-first + External):** `cellular/services/tower_resolver.py`
  - ابتدا lookup دقیق در DB (`mcc/mnc/cell_id[/lac]`)
  - سپس lookup امضایی (neighbor-style) با `pci` (+ earfcn/lac اختیاری)
  - سپس در صورت مجاز بودن: Combain/Google و upsert به DB + ثبت در `TowerLookupLog`

### Endpointهای اصلی
در `cellular/urls.py` (همه زیر `towercell/urls.py` با پیشوند `/api/`):
- `POST /api/locate/` محاسبه موقعیت از لیست سل‌ها
- `POST /api/towers/add/` ایجاد یک دکل (فعلاً بدون محدودیت دسترسی مشخص در view)
- `POST /api/towers/search/` جستجوی دکل‌ها
- `POST /api/towers/within/` دکل‌ها داخل bounding box (برای نقشه)
- `POST /api/towers/import/` Import مستقیم CSV (با API Key)
- `POST /api/towers/import-start/` Import شبه-async (thread) + `GET /api/towers/import-status/<job_id>/`
- `POST /api/snapshot/locate/` دریافت Snapshot از endpoint خارجی (با allowlist ضد SSRF) و locate
- `GET /api/system/db-info/` اطلاعات DB (در `DEBUG=True` عمومی است)
- `POST /api/calibrate/` محاسبه `n_effective` با ground-truth
- `POST /api/ref_loss/` تخمین `REF_LOSS` از EARFCN/فرکانس

---

## 3) خلاصه فرانت‌اند (Frontend Summary)

### تکنولوژی/قابلیت‌ها
- React + Vite + Leaflet (`front/`)
- قابلیت‌ها:
  - نقشه + پین‌ها + دایره‌ها + خط‌کش
  - دریافت Markerهای دکل در محدوده‌ی نقشه (`/api/towers/within/`)
  - Import CSV (start + polling)
  - Snapshot Locate (ارسال endpoint + snapshot_id و نمایش جدول سل‌ها و نتایج)
  - بخش AI برای ساخت پین از متن (Gemini)

### سرویس‌های سمت فرانت
- `front/services/towerService.ts`
  - `fetchTowersByBounds`
  - `startImport` + `fetchImportStatus`
- `front/services/snapshotService.ts`
  - `locateFromSnapshot`
- `front/services/geminiService.ts`
  - استفاده از `@google/genai` و `googleSearch` tool

### نکته مهم UI/Build
`front/index.html` از Tailwind CDN استفاده می‌کند و یک `importmap` هم دارد؛ در کنار Vite این ترکیب ممکن است رفتار build/dev را پیچیده کند (و `index.css` هم لینک شده ولی فایلش موجود نیست).

---

## 4) مشکلات و ریسک‌ها (Issues/Risks)

### A) ریسک‌های مهم (High Priority)
1) **مشکل جدی در Serialization پاسخ locate**
   - در `cellular/services/locator.py` در حالت ۲ دکل و ۳+ دکل، `debug.bearing_used` و/یا `debug.signal` مقدار `None` دارند.
   - اما در `cellular/serializers.py`، فیلدهای `bearing_used` (FloatField) و `signal` (IntegerField) `allow_null` ندارند.
   - نتیجه: امکان 500 هنگام ساخت پاسخ (به‌خصوص در `LocateUserView` و `SnapshotLocateView`).

2) **افشای کلید Gemini در فرانت**
   - `front/vite.config.ts` کلید `GEMINI_API_KEY` را به `process.env.*` در باندل تزریق می‌کند و `front/services/geminiService.ts` آن را در مرورگر استفاده می‌کند.
   - این یعنی کلید به کاربر نهایی لو می‌رود و قابل سوءاستفاده/هزینه‌زا است.

3) **پیکربندی امنیتی Django برای production آماده نیست**
   - `towercell/settings.py` دارای `DEBUG=True` و `ALLOWED_HOSTS=['*']` و `SECRET_KEY` هاردکد است.
   - در production باید با env کنترل شود، وگرنه ریسک امنیتی/نشت اطلاعات دارد.

4) **Import و Jobها برای فایل‌های بزرگ مقیاس‌پذیر نیست**
   - `import_towers_from_csv` کل CSV را اول normalize می‌کند و در RAM نگه می‌دارد (برای فایل‌های بزرگ ایران عملی نیست).
   - Job status در `cellular/utils/import_jobs.py` فقط in-memory است؛ با ری‌استارت یا multi-worker از بین می‌رود.

### B) مشکلات عملکردی/دقت (Medium Priority)
1) **کیفیت/دقت مدل Path Loss و استفاده از پارامترها**
   - در حالت ۲ دکل، فاصله‌ها با `calculate_distance` بدون `tx_power` دکل محاسبه می‌شوند (پیش‌فرض‌ها).
   - بهتر است برای هر دکل از `tx_power` همان دکل استفاده شود و وزن‌دهی/کالیبراسیون واقعی اضافه شود.

2) **`earfcn_to_freq_mhz` احتمال خطای منطقی دارد**
   - بازه‌ی `70..6000` را «فرکانس MHz» فرض می‌کند، درحالی‌که EARFCNهای LTE (مثل 1300/1650/…) دقیقاً داخل همین بازه‌اند ولی EARFCN هستند نه MHz.
   - این موضوع خروجی `ref_loss` را اشتباه می‌کند.

3) **`fetch_and_save_tower` کش `TowerResolver` را دور می‌زند**
   - این wrapper هر بار یک `TowerResolver` جدید می‌سازد، پس cache per-request عملاً بی‌اثر می‌شود (به‌خصوص در `SnapshotLocateView` که حلقه‌های زیاد دارد).

4) **Endpointهای عمومی بدون محدودیت**
   - `towers/add`, `towers/search`, `towers/within`, `locate`, `snapshot/locate` همگی عملاً بدون auth/limit هستند (به‌جز import که API key دارد).
   - در صورت public شدن API، نیاز به throttle/rate-limit و auth جدی است.

### C) مشکلات داده/DB (Medium → Low)
1) **Unique constraint با فیلدهای nullable**
   - `unique_together = (mcc, mnc, cell_id, lac)` با `lac=None` در PostgreSQL اجازه‌ی چند رکورد تکراری می‌دهد (Null ها distinct هستند).
   - این می‌تواند `get_or_create` و lookupها را ambiguous کند.

2) **Indexهای ناکافی برای Queryهای رایج**
   - `towers/within` روی `lat/lon` فیلتر می‌زند ولی index مناسب ندارد (برای دیتای بزرگ کند می‌شود).
   - در عمل بهتر است PostGIS + GiST index روی Point داشته باشید.

---

## 5) پیشنهادهای بهبود (به ترتیب اولویت)

### فاز 1: تثبیت (۱–۳ روز)
- اصلاح قرارداد پاسخ `debug`:
  - یا serializer را با `allow_null=True` هماهنگ کنید
  - یا همیشه مقدار عددی بدهید و `confidence` را هم در همه حالات برگردانید
- کنترل production settings:
  - `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, CORS/CSRF فقط از env
  - خاموش کردن یا محدودسازی `DbInfoView` در production
- محدودسازی endpointهای حساس:
  - حداقل برای `towers/add` و `import` و `snapshot/locate` auth/api-key + rate limit

### فاز 2: مقیاس‌پذیری داده و Job (۳–۷ روز)
- بازنویسی Import به صورت stream/chunk:
  - پردازش CSV به chunkهای کوچک و `bulk_create/bulk_update` مرحله‌ای
  - حذف `normalized_rows` بزرگ در RAM
- جایگزینی job state in-memory با:
  - Redis (ساده) یا DB table (پایدار) یا Celery result backend
- استفاده از Celery (هم‌اکنون در dependencies هست) برای import و کارهای سنگین

### فاز 3: افزایش دقت locate (۱–۳ هفته)
- بهبود ۲-tower و ۳+-tower:
  - استفاده‌ی بهتر از NLLS با بیش از ۳ دکل (نه فقط top3)
  - وزن‌دهی ترکیبی بر اساس RSRP/RSRQ/TA و residualها
  - تولید confidence واقعی (مثلاً از RMS residual و هندسه‌ی دکل‌ها)
- تصحیح/تکمیل mapping EARFCN→Frequency (یا گرفتن مستقیم فرکانس/باند از ورودی)
- بهبود مدل داده:
  - جدا کردن LTE/UMTS/GSM در resolver و upsert (نه همه LTE)

### فاز 4: فرانت امن‌تر و قابل نگهداری‌تر (۳–۷ روز)
- انتقال Gemini به backend (proxy endpoint) یا حذف کلید از فرانت
- یکدست‌سازی build:
  - حذف `importmap` از `front/index.html` و تکیه بر Vite bundling
  - اصلاح `index.css` (یا حذف لینک) و نصب Tailwind به روش استاندارد Vite
- بهبود UX:
  - مدیریت cancel/out-of-order برای `fetchTowersByBounds`
  - نمایش circle دقت/شعاع برای `computed.radius` روی نقشه

---

## 6) پیشنهادهای تست/کیفیت (Quality Gates)
- تست واحد برای:
  - `clean_cells` (sentinelها و رنج RSRP)
  - `earfcn_to_freq_mhz` و `estimate_ref_loss_from_earfcn`
  - `trilaterate_three` (سناریوهای ساده با جواب معلوم)
- تست API (حداقل smoke):
  - `/api/locate/` برای ۱/۲/۳ دکل و اطمینان از عدم 500
- سنجه‌های عملی:
  - Median error (m) روی دیتای snapshotها
  - نرخ «tower resolved» از DB vs external
  - هزینه/تعداد callهای external (Combain/Google)

---

## 7) نکات مهمی که باید «یادمان بماند»
- قرارداد پاسخ `debug` باید با serializer هماهنگ شود (الان ریسک 500 دارد).
- کلیدهای AI نباید سمت کلاینت باشند.
- Import برای دیتای ایران باید chunk/stream باشد؛ مدل in-memory فعلی به دیتای بزرگ نمی‌خورد.
- برای سرعت `towers/within` در دیتای بزرگ، PostGIS و index فضایی تقریباً ضروری است.
- snapshot locate با allowlist ضد SSRF خوب شروع شده، ولی باید کنترل هزینه‌ی external lookups و caching جدی‌تر شود.

