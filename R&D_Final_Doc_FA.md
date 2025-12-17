<div dir="rtl" lang="fa">

# ${\color{#FF5656}\textsf{مکان‌یابی دکل‌های مخابراتی (Cell Towers Locating)}}$

_**Cellular Positioning**_ به طور کلی بر ۳ روش اصلی استوار است که جایگزینی برای **Network-Based Positioning** محسوب می‌شوند:

> ۱. **Cell ID (Coarse):** ساده‌ترین روش. موقعیت دکل سرویس‌دهنده (Serving Cell) را برمی‌گرداند. (دقت پایین)
> 
> ۲. **RSSI / RSRP (Signal Strength):** تخمین فاصله بر اساس قدرت سیگنال. هر چه سیگنال ضعیف‌تر باشد، فاصله دورتر است. (دقت متوسط)
> 
> ۳. **TDoA / ToF (Time Difference of Arrival):** محاسبه دقیق زمان رفت و برگشت سیگنال بین گوشی و چندین دکل برای مثلث‌بندی (Triangulation). (دقت بالا، ریاضیات پیچیده)

# ${\color{#FFA239}\textsf{بخش ۱: تکامل شبکه و مکانیسم‌ها}}$

درک نحوه ارتباط نسل‌های مختلف برای انتخاب پارامترهای صحیح مکان‌یابی حیاتی است.

# ${\color{#FEEE91}\textsf{۱. مکانیسم‌های مکان‌یابی نسل ۲ (GSM - BTS)}}$

## ${\color{#8CE4FF}\textsf{مکانیسم ارتباطی (TDMA)}}$

در GSM، همگام‌سازی (Synchronization) کلید جلوگیری از برخورد سیگنال در اسلات‌های زمانی است.

- **Downlink (Tower -> Phone):** دکل (BTS) سیگنال‌های همگام‌سازی و فرمان **Timing Advance (TA)** را ارسال می‌کند.
    
- **Uplink (Phone -> Tower):** ایستگاه موبایل (MS) یک **Access Burst** ارسال می‌کند. دکل تاخیر زمان رسیدن را اندازه‌گیری می‌کند تا فاصله را محاسبه کند.
    

## ${\color{#8CE4FF}\textsf{پارامترهای کلیدی}}$

۱. **CGI (Cell Global Identity):** شناسه یکتا (MCC-MNC-LAC-CID). ۲. **TA (Timing Advance):** بازه ۰ تا ۶۳. دقت حدود ۵۵۰ متر به ازای هر واحد (دقت پایین). ۳. **RXLEV:** سطح سیگنال دریافتی (dBm). ۴. **BSIC:** کد شناسایی ایستگاه پایه (تمایز سلول‌های همسایه).

# ${\color{#FEEE91}\textsf{۲. مکانیسم‌های مکان‌یابی نسل ۳ (UMTS/WCDMA - NodeB)}}$

## ${\color{#8CE4FF}\textsf{مکانیسم ارتباطی (CDMA)}}$

تمام دکل‌ها به طور همزمان روی یک فرکانس با استفاده از کدهای منحصر به فرد ارسال می‌کنند.

- **چالش (Hearability):** سیگنال‌های قوی از سلول سرویس‌دهنده می‌توانند سیگنال‌های همسایه را غرق کنند (مشکل Near-Far).
    
- **راه حل (IPDL):** شبکه از **Idle Period Downlink** استفاده می‌کند. NodeB سرویس‌دهنده برای لحظاتی ارسال را متوقف می‌کند تا UE بتواند سیگنال‌های ضعیف‌تر همسایه را از طریق **CPICH** تشخیص دهد.
    

## ${\color{#8CE4FF}\textsf{پارامترهای کلیدی}}$

۱. **PSC (Primary Scrambling Code):** شناسه یکتا برای NodeB. ۲. **RSCP (Received Signal Code Power):** قدرت سیگنال پایلوت CPICH. معیار اصلی برای Path Loss. ۳. **RTT (Round Trip Time):** جایگزین TA برای محاسبه فاصله.

# ${\color{#FEEE91}\textsf{۳. مکانیسم‌های مکان‌یابی نسل ۴ (LTE - eNodeB)}}$

## ${\color{#8CE4FF}\textsf{مکانیسم ارتباطی (OFDMA \\& PRS)}}$

LTE طیف فرکانسی را به عنوان یک شبکه زمان-فرکانس (Time-Frequency Grid) در نظر می‌گیرد.

- **Downlink:** شبکه سیگنال‌های اختصاصی **PRS (Positioning Reference Signals)** را ارسال می‌کند. این سیگنال‌ها طوری چیده شده‌اند که تداخل نداشته باشند و تشخیص چندین دکل را ممکن سازند.
    
- **Uplink:** دستگاه کاربر (UE) مقدار **RSTD (Reference Signal Time Difference)** را برای محاسبه OTDOA اندازه‌گیری می‌کند.
    

## ${\color{#8CE4FF}\textsf{پارامترهای کلیدی}}$

۱. **PCI (Physical Cell ID):** شناسه فیزیکی یکتا (بازه: ۰-۵۰۳). ۲. **RSRP (Reference Signal Received Power):** میانگین خطی قدرت سیگنال‌های مرجع. پایدارتر از RSSI. ۳. **TA (Timing Advance):** بازه ۰ تا ۱۲۸۲. دقت **~۷۸ متر** به ازای هر واحد (دقت بالا).

# ${\color{#FEEE91}\textsf{۴. مکانیسم‌های مکان‌یابی نسل ۵ (5G NR - gNodeB)}}$

## ${\color{#8CE4FF}\textsf{مکانیسم ارتباطی (Beamforming)}}$

5G تغییر پارادایمی از پخش همه‌جهته (Omnidirectional) به **Beamforming** جهت‌دار دارد.

- **Downlink:** دکل gNodeB بلوک‌های سیگنال همگام‌سازی (SSB) را در پرتوهای متوالی ارسال می‌کند (Beam Sweeping).
    
- **Measurement:** دستگاه UE شاخص **Best Beam** را شناسایی می‌کند که **جهت زاویه‌ای** کاربر را به شبکه می‌دهد.
    

## ${\color{#8CE4FF}\textsf{پارامترهای کلیدی}}$

۱. **Beam ID (SSB Index):** نماینده اصلی برای **جهت/زاویه**. ۲. **SS-RSRP:** قدرت دریافتی پرتو SSB خاص. ۳. **AoA / AoD:** زاویه ورود / خروج (حیاتی برای مثلث‌بندی هندسی). ۴. **نکته داده‌ها:** داده‌های باز (Open Data) برای 5G کمیاب است؛ اغلب از "4G Fallback" برای مکان‌یابی استفاده می‌شود.

# ${\color{#FFA239}\textsf{بخش ۲: جمع‌آوری داده‌ها (Data Acquisition)}}$

برای مکان‌یابی کاربر، ابتدا باید دکل‌های قابل مشاهده را شناسایی کرده و آن‌ها را به مختصات فیزیکی نگاشت کنیم.

# ${\color{#FEEE91}\textsf{دکود کردن سیگنال‌ها (آنچه گوشی می‌بیند)}}$

دکل‌های مخابراتی بسته‌های **System Information Blocks (SIB)** را پخش می‌کنند. حتی بدون سیم‌کارت، دستگاه می‌تواند موارد زیر را دکود کند:

## ${\color{#8CE4FF}\textsf{الف) پارامترهای هویتی (آدرس)}}$

- **MCC:** کد کشور موبایل (مثلاً ۴۳۲ برای ایران).
    
- **MNC:** کد شبکه موبایل (مثلاً ۱۱ برای همراه اول).
    
- **LAC/TAC:** کد ناحیه مکانی/ردیابی.
    
- **CID/ECI:** شناسه یکتای سلول.
    

## ${\color{#8CE4FF}\textsf{ب) سیگنال و زمان‌بندی}}$

- **RSSI/RSRP:** بلندی صدای دکل (معیار فاصله).
    
- **TA/ToA:** تاخیر سیگنال (معیار زمانی فاصله).
    

# ${\color{#FEEE91}\textsf{منابع داده (نگاشت ID به مختصات)}}$

از آنجا که دکل‌ها مختصات Lat/Lon خود را پخش نمی‌کنند، ما از پایگاه‌داده‌های خارجی استفاده می‌کنیم.

## ${\color{#8CE4FF}\textsf{الف) پایگاه‌داده‌های متن‌باز (Open Source)}}$

- **OpenCellID:** بزرگترین پایگاه‌داده باز. خوب برای 2G/3G/4G. ضعیف در 5G.
    
- **Mozilla Location Service (MLS):** _بازنشسته شده (۲۰۲۴)._ دیگر منبع معتبری نیست.
    

## ${\color{#8CE4FF}\textsf{ب) APIهای تجاری}}$

- **Google Geolocation API / Unwired Labs:** دقت بالا، پشتیبانی از 5G، سرویس‌های پولی.
    

## ${\color{#8CE4FF}\textsf{ج) "War Driving" (جمع‌آوری دستی)}}$

برای شبکه‌های خصوصی یا نیازهای با دقت بالا (مانند پردیس‌های خاص)، باید پایگاه‌داده خود را بسازید. برای اطمینان از کیفیت داده و قابلیت پس‌پردازش، ساختار (Schema) باید قوی باشد.

- **روش:** رانندگی/پیاده‌روی با یک اپلیکیشن لاگر که **Cell ID + GPS** را ضبط می‌کند.
    
- **"لیست داده‌های طلایی" برای ثبت (Database Schema):**
    
    ۱. **Radio Type:** حیاتی برای تعیین استاندارد (GSM/LTE/5G). ۲. **Identifiers:** شناسه‌های MCC, MNC, LAC/TAC, CID/ECI. ۳. **Physical ID:** پارامتر PCI (LTE/5G) یا PSC (UMTS). حیاتی برای تفکیک سلول‌های همسایه که CID آن‌ها دکود نشده است. ۴. **Signal Strength:** مقدار RSRP (dBm) برای LTE و RSSI برای نسل‌های قبل. ۵. **Signal Quality:** پارامتر RSRQ/SNR. کمک به فیلتر کردن اندازه‌گیری‌های "نویزی". ۶. **Timing Advance (TA):** اگر موجود باشد، فاصله مستقیم را می‌دهد (۰-۱۲۸۲). ۷. **GPS Location:** عرض جغرافیایی، طول جغرافیایی، ارتفاع (برای اصلاح سه بعدی). ۸. **GPS Accuracy:** اگر خطا بیشتر از ۲۰ متر بود، داده دور ریخته شود. ۹. **Speed & Bearing:** کمک به اصلاح اثر داپلر یا فیلتر کردن اندازه‌گیری‌های هنگام حرکت خیلی سریع. ۱۰. **Device Info:** مدل و نسخه سیستم عامل. چیپ‌های مختلف قدرت سیگنال را متفاوت گزارش می‌دهند؛ این فیلد امکان کالیبراسیون را می‌دهد.
    

**پیاده‌سازی مدل Django:**

```
from django.db import models

class CellMeasurement(models.Model):
    RADIO_CHOICES = [
        ('gsm', 'GSM'), ('wcdma', 'WCDMA'), ('lte', 'LTE'), ('nr', '5G NR')
    ]

    # --- Identity ---
    radio = models.CharField(max_length=10, choices=RADIO_CHOICES)
    mcc = models.IntegerField()
    mnc = models.IntegerField()
    lac_tac = models.IntegerField(help_text="Location/Tracking Area Code")
    cell_id = models.BigIntegerField(help_text="CID or ECI")
    pci = models.IntegerField(null=True, blank=True, help_text="Physical Cell ID / PSC")

    # --- Signal Metrics ---
    rsrp = models.FloatField(help_text="Signal Power (dBm)")
    rsrq = models.FloatField(null=True, blank=True, help_text="Signal Quality")
    ta = models.IntegerField(null=True, blank=True, help_text="Timing Advance")
    
    # --- Location (Ground Truth) ---
    lat = models.FloatField()
    lon = models.FloatField()
    altitude = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(help_text="GPS Accuracy in meters")
    
    # --- Metadata ---
    speed = models.FloatField(null=True, blank=True, help_text="Device speed in m/s")
    bearing = models.FloatField(null=True, blank=True, help_text="Movement direction (0-360)")
    device_model = models.CharField(max_length=100, help_text="e.g. Pixel 6 Pro")
    timestamp = models.DateTimeField(auto_now_add=True)
    is_serving = models.BooleanField(default=False, help_text="True if connected, False if neighbor")

    class Meta:
        indexes = [
            models.Index(fields=['mcc', 'mnc', 'lac_tac', 'cell_id']),
            models.Index(fields=['lat', 'lon']),
        ]
```

# ${\color{#FFA239}\textsf{بخش ۳: چالش‌های فنی و پیش‌پردازش}}$

قبل از اجرای الگوریتم‌ها، داده‌های خام مودم باید پاکسازی شوند. APIهای اندروید (`getAllCellInfo`) اغلب خطاهایی برمی‌گردانند که باعث اشتباهات فاحش می‌شود.

# ${\color{#FEEE91}\textsf{۱. پدیده "سلول شبح" (The Ghost Cell Phenomenon) 👻}}$

مودم‌ها مصرف باتری را اولویت می‌دهند. آن‌ها **لایه فیزیکی** سلول‌های همسایه (قدرت سیگنال) را مانیتور می‌کنند اما اغلب از دکود کردن **لایه داده** (هویت) صرف‌نظر می‌کنند.

- **نشانه:** شما `RSRP` و `PCI` را دارید، اما `MNC` یا `CID` نامعتبر هستند.
    
- **راه حل:**
    
    - _پایه:_ این سلول‌ها را فیلتر کنید.
        
    - _پیشرفته:_ استفاده از تطبیق PCI اگر پایگاه‌داده با کیفیتی دارید.
        

# ${\color{#FEEE91}\textsf{۲. مقادیر Sentinel (مصنوعات داده) 🐞}}$

وقتی مودم در خواندن مقداری شکست می‌خورد، مقادیر خاص "Max Values" را برمی‌گرداند. این‌ها باید فیلتر شوند.

| **Parameter** | **Invalid Value** | **Reason** | | **MCC/MNC** | `2147483647` | `Integer.MAX_VALUE` (Identity not decoded) | | **TAC** | `65535` | 16-bit Overflow (`0xFFFF`) | | **CI** | `268435455` | 28-bit Max Value |

**منطق فیلتر کردن (شبه‌کد):**

```
if (cell.mcc == Int.MAX_VALUE || cell.ci == Int.MAX_VALUE) {
    continue; // Skip Ghost Cell
}
```

# ${\color{#FEEE91}\textsf{۳. مشکل جهت‌داری (Sectorization) 🍕}}$

دکل‌ها همه‌جهته (Omnidirectional) نیستند. آن‌ها معمولاً به ۳ سکتور (هر کدام ۱۲۰ درجه) تقسیم می‌شوند. از آنجا که Azimuth به ندرت عمومی است، ما از روش‌های ابتکاری (Heuristics) بر اساس **ساختار Cell ID** استفاده می‌کنیم:

**الف) قانون "رقم آخر" (GSM/UMTS/Legacy)** رایج در شبکه‌های قدیمی یا تنظیمات استاندارد وندورهای خاص (مثل Huawei/Ericsson).

- **منتهی به ۱ (یا ۰):** سکتور ۱ $\leftarrow$ شمال/شمال‌شرقی ($۰^\circ-۱۲۰^\circ$)
    
- **منتهی به ۲ (یا ۱):** سکتور ۲ $\leftarrow$ جنوب‌شرقی ($۱۲۰^\circ-۲۴۰^\circ$)
    
- **منتهی به ۳ (یا ۲):** سکتور ۳ $\leftarrow$ غرب ($۲۴۰^\circ-۳۶۰^\circ$)
    

**ب) قانون Modulo-256 (LTE/5G)** در LTE، شناسه ۲۸ بیتی ECI ترکیبی از eNodeB ID و Local Cell ID است.

- **فرمول:** $\text{Local Cell ID} = \text{ECI} \pmod{256}$
    
- **تفسیر:**
    
    - **۰، ۱، ۲:** اغلب مربوط به سکتورهای ۱، ۲، ۳ (باند اصلی) هستند.
        

**ج) قانون "ترکیبی" (Multi-Band LTE)** زمانی استفاده می‌شود که اپراتورها باندها را با استفاده از آفست در Local Cell ID روی هم می‌چینند (مثلاً باند A=۱-۳، باند B=۱۱-۱۳).

- **منطق:** ابتدا Local ID را جدا کنید (`ECI % 256`). سپس رقم آخر را استخراج کنید (modulo 10) تا آفست باند حذف شود.
    
- **چرا؟** یک Local ID برابر `۱۱` یعنی "سکتور ۱، باند ۲". عدد `۱` (از ۱۱) نشان‌دهنده جهت است.
    

**پیاده‌سازی پایتون:**

```
def get_hybrid_sector(cell_id):
    # 1. Extract Local Cell ID (8-bit)
    local_id = int(cell_id) % 256

    # 2. Extract Last Digit (Strips Band Offsets like 10, 20)
    sector_digit = local_id % 10

    if sector_digit in [1, 0]: return "North/NE"
    if sector_digit in [2]:    return "South-East"
    if sector_digit in [3]:    return "West"
    return "Unknown"
```

# ${\color{#FFA239}\textsf{بخش ۴: الگوریتم‌های مکان‌یابی}}$

پس از تمیزکاری داده‌ها، بر اساس تعداد دکل‌های قابل مشاهده الگوریتم مناسب را انتخاب می‌کنیم.

# ${\color{#FEEE91}\textsf{سناریو A: تک دکل (Geometric Sector Projection)}}$

**شرط:** تنها ۱ دکل معتبر قابل مشاهده است. **منطق:** به جای فرض اینکه کاربر _روی_ دکل است، موقعیت او را بر اساس فاصله تخمینی و "زاویه نیمساز" سکتور (Azimuth) به بیرون تصویر (Project) می‌کنیم.

۱. **جستجو:** مختصات Lat/Lon دکل. ۲. **تخمین فاصله (**$d$**):** استفاده از Timing Advance (TA) یا فرمول Path Loss. ۳. **تعیین جهت (**$\theta$**):** استفاده از روش ابتکاری سکتور برای یافتن زاویه مرکزی پرتو.

- سکتور ۱: $\approx ۶۰^\circ$
    
- سکتور ۲: $\approx ۱۸۰^\circ$
    
- سکتور ۳: $\approx ۳۰۰^\circ$ ۴. **تصویرسازی هندسی:** محاسبه مختصات جدید $(lat_{new}, lon_{new})$ با حرکت به اندازه فاصله $d$ در جهت زاویه $\theta$ از دکل.
    
- _نکته:_ این کار کاربر را در "مرکز ثقل" برش سکتور قرار می‌دهد و حداکثر خطا را نسبت به موقعیت دکل کاهش می‌دهد.
    

# ${\color{#FEEE91}\textsf{سناریو B: دو دکل (Weighted Centroid \\& Geometric Intersection)}}$

**شرط:** ۲ لنگر (Anchor) متمایز (مثلاً دو سیم‌کارت یا سرویس‌دهنده + ۱ همسایه قوی). با تنها دو نقطه مرجع، مثلث‌بندی استاندارد غیرممکن است (بی‌نهایت جواب). ما از یکی از دو روش زیر استفاده می‌کنیم:

**روش ۱: مرکز ثقل وزن‌دار بهبودیافته (Enhanced Weighted Centroid) - سریع** به جای قرار دادن کاربر روی خط مستقیم بین دکل‌ها، با استفاده از فاکتور درجه ($g$) موقعیت را به صورت نمایی به سمت سیگنال قوی‌تر می‌کشیم.

- **فرمول:**
    
    $$Lat_{user} = \frac{\sum (Lat_i \cdot w_i)}{\sum w_i}$$
- **وزن (**$w_i$**):** $w_i = \frac{1}{(d_i)^g}$
    
    - که در آن $d_i$ فاصله تخمینی است.
        
    - $g$ فاکتور درجه است (معمولاً $g \approx ۱-۲$).
        

**روش ۲: تقاطع هندسی (Geometric Intersection) - دقیق** دو دایره در **دو نقطه** همدیگر را قطع می‌کنند. ما هر دو را محاسبه کرده و با استفاده از منطق سکتور، نقطه نامعتبر را حذف می‌کنیم.

۱. **محاسبه نقاط تقاطع:** دو نقطه‌ای که شعاع دایره‌ها ($r_1, r_2$) تلاقی می‌کنند را بیابید. ۲. **فیلتر با سکتور:** بررسی کنید کدام نقطه در "مخروط دید" (Sector Azimuth) دکل‌ها قرار می‌گیرد.

**پیاده‌سازی پایتون (تقاطع دایره):**

```
import math

def get_circle_intersections(x0, y0, r0, x1, y1, r1):
    # Distance between centers
    d = math.sqrt((x1-x0)**2 + (y1-y0)**2)
    
    # Check for solvability
    if d > r0 + r1: return [] # Separate circles
    if d < abs(r0 - r1): return [] # One inside other
    if d == 0: return [] # Concentric
    
    # Calculate 'a' distance to the radical line
    a = (r0**2 - r1**2 + d**2) / (2*d)
    h = math.sqrt(r0**2 - a**2)
    
    # Point P2 (intersection of radical line and center line)
    x2 = x0 + a * (x1 - x0) / d
    y2 = y0 + a * (y1 - y0) / d
    
    # Two intersection points (P3_1, P3_2)
    x3_1 = x2 + h * (y1 - y0) / d
    y3_1 = y2 - h * (x1 - x0) / d
    
    x3_2 = x2 - h * (y1 - y0) / d
    y3_2 = y2 + h * (x1 - x0) / d
    
    return [(x3_1, y3_1), (x3_2, y3_2)]

# Logic to pick the best point:
# 1. Calculate Azimuth from Tower 1 to each Point.
# 2. Compare with Tower 1's Sector Angle.
# 3. Select the point that "faces" the sector.
```

# ${\color{#FEEE91}\textsf{سناریو C: سه دکل و بیشتر (Advanced Trilateration)}}$

**شرط:** ۳ یا بیشتر لنگر (Anchor) حل شده. **منطق:** یافتن تقاطع چندین دایره. در دنیای واقعی، اندازه‌گیری‌ها نویزی هستند، بنابراین دایره‌ها به ندرت دقیقاً در یک نقطه قطع می‌شوند. ما باید خطا را حداقل کنیم.

**روش ۱: سیستم خطی‌شده (Basic)** معادلات را از هم کم می‌کند تا جملات مربعی حذف شوند. سریع اما حساس به نویز.

- **ریاضی:** $A \cdot x + B \cdot y = C$
    

**روش ۲: حداقل مربعات غیرخطی (Non-Linear Least Squares - Pro)** استفاده از بهینه‌سازی تکراری (مانند Levenberg-Marquardt) برای یافتن $(x, y)$ که مجموع خطاهای مربعی بین فواصل اندازه‌گیری شده و محاسبه شده را به حداقل برساند.

- **فرمول برای مینیمم‌سازی:**
    
    $$S = \sum_{i=1}^{n} (\sqrt{(x-x_i)^2 + (y-y_i)^2} - d_i)^2$$

**پیاده‌سازی پایتون (NLLS با Scipy):**

```
from scipy.optimize import least_squares
import numpy as np

def residuals(guess, towers):
    """
    Calculate the difference between calculated distance (from guess)
    and measured distance (from RSRP/TA).
    """
    x_g, y_g = guess
    res = []
    for t in towers:
        dist_calc = np.sqrt((x_g - t.lat)**2 + (y_g - t.lon)**2)
        res.append(dist_calc - t.radius_km)
    return res

def trilaterate_nlls(towers):
    # Initial guess: Weighted Centroid
    x0, y0 = calculate_weighted_centroid(towers)
    
    # Optimization
    result = least_squares(residuals, x0=[x0, y0], args=(towers,))
    return result.x # [lat, lon]
```

# ${\color{#FEEE91}\textsf{سناریو D: چالش ساختمان‌های بلند (Barometric Altimetry) 🏢}}$

**مشکل:** در آسمان‌خراش‌ها، گوشی به دکل‌های دوردست LoS متصل می‌شود. الگوریتم‌های استاندارد دو بعدی شکست می‌خورند زیرا **Slant Range** (وتر) به طور قابل توجهی طولانی‌تر از **Ground Distance** (ضلع افقی) است. **راه حل:** استفاده از فشارسنج (Barometer) دستگاه برای محاسبه ارتفاع ($z$) و اصلاح فاصله.

**گام ۱: محاسبه ارتفاع (فرمول بارومتریک)** استفاده از فرمول بارومتریک بین‌المللی برای تخمین ارتفاع از سطح دریا یا نسبت به طبقه همکف.

$$h = 44330 \cdot \left(1 - \left(\frac{P}{P_0}\right)^{\frac{1}{5.255}}\right)$$

- $P$: فشار اندازه‌گیری شده (hPa).
    
- $P_0$: فشار مرجع (سطح دریا یا طبقه همکف).
    

**گام ۲: اصلاح سه بعدی به دو بعدی (Slant Range)** تبدیل شعاع اندازه‌گیری شده (وتر) به شعاع زمینی (ضلع) برای ترسیم دقیق روی نقشه.

$$d_{ground} = \sqrt{d_{slant}^2 - (h_{tower} - h_{user})^2}$$

**پیاده‌سازی پایتون (ارتفاع و طبقه):**

```
def calculate_altitude(pressure_hpa, p0=1013.25):
    """
    Returns altitude in meters using International Barometric Formula.
    """
    return 44330 * (1 - (pressure_hpa / p0)**0.1903)

def estimate_floor(current_pressure, ground_pressure):
    """
    Estimates floor number based on pressure difference.
    Approx 1 floor = 3 meters = ~0.35 hPa drop (varies by altitude).
    """
    h_current = calculate_altitude(current_pressure, ground_pressure)
    floor_height = 3.5 # meters (approx for office buildings)
    return int(h_current / floor_height)

def correct_slant_range(measured_dist_km, tower_h_m, user_h_m):
    """
    Converts 3D slant range to 2D map distance.
    """
    h_diff_km = abs(tower_h_m - user_h_m) / 1000.0
    if measured_dist_km <= h_diff_km:
        return 0.0 # User is directly under/above tower
    return math.sqrt(measured_dist_km**2 - h_diff_km**2)
```

# ${\color{#FFA239}\textsf{بخش ۵: مدل‌های ریاضی و پیاده‌سازی}}$

# ${\color{#FEEE91}\textsf{۱. فیزیک: کالیبراسیون و Path Loss}}$

برای تبدیل قدرت سیگنال (RSRP) به فاصله ($d$)، از مدل Log-Distance Path Loss استفاده می‌کنیم.

## ${\color{#8CE4FF}\textsf{فرمول}}$

$$d = 10^{\frac{(TX - RSRP) - REF\_LOSS}{10 \cdot n}}$$

- **TX:** قدرت ارسال دکل (پیش‌فرض $\approx ۴۰-۴۵$ dBm).
    
- **RSRP:** سیگنال اندازه‌گیری شده در سمت کاربر.
    
- **REF_LOSS:** افت سیگنال در فاصله ۱ متری. محاسبه می‌شود به صورت: $20 \log_{10}(f_{MHz}) + 32.44 - G_t - G_r$.
    
- **n (Exponent):** فاکتور محیطی.
    
    - فضای آزاد: ۲.۰
        
    - شهری: ۳.۵ - ۴.۰
        

## ${\color{#8CE4FF}\textsf{کالیبراسیون (یافتن n)}}$

اگر یک نقطه مرجع (GPS) و خوانش سیگنال دارید، می‌توانید فرمول را معکوس کنید تا $n$ موثر برای منطقه خود را بیابید:

$$n_{effective} = \frac{(TX - RSRP) - REF\_LOSS}{10 \cdot \log_{10}(d_{GPS})}$$

# ${\color{#FEEE91}\textsf{۲. جزئیات تخمین‌گر REF\\_LOSS (افت مسیر مرجع در ۱ متر)}}$

**هدف:** تولید یک مقدار معقول برای `REF_LOSS` (dB) زمانی که ثابتِ هر سایت ناشناخته است. این مقدار نشان‌دهنده افت مورد انتظار در فضای آزاد (به علاوه تلفات سیستم) در فاصله مرجع ۱ متر است و به عنوان ثابت جمعی در مدل Path Loss استفاده می‌شود.

## ${\color{#8CE4FF}\textsf{رویکرد پیاده‌سازی شده}}$

۱. **تبدیل فرکانس:** تبدیل `earfcn` (اگر موجود باشد) به فرکانس Downlink بر حسب MHz با استفاده از جدول باند.

۲. **محاسبه FSPL در ۱ متر:** تخمین‌گر از رابطه افت مسیر فضای آزاد (FSPL) بر حسب dB پیروی می‌کند:

$$\mathrm{FSPL}_{1\mathrm{m}} = 20\,\log_{10}(f_{\mathrm{MHz}}) + 32.44$$

۳. **تنظیم برای بهره‌ها و تلفات:** پروژه FSPL را با بهره آنتن‌ها و تلفات سیستم تنظیم می‌کند تا ثابت افت مرجع را تولید کند:

$$\mathrm{REF\_LOSS} = \mathrm{FSPL}_{1\mathrm{m}} - G_t - G_r + L_{\mathrm{sys}}$$

- $G_t$: بهره آنتن فرستنده (dBi).
    
- $G_r$: بهره آنتن گیرنده (dBi).
    
- $L_{\mathrm{sys}}$: مجموع تلفات کابل/سیستم (dB).
    

**نکته کاربردی:** این تخمین‌گر یک روش ابتکاری مبتنی بر فیزیک (FSPL) است و باید به عنوان مقدار اولیه استفاده شود. برای بهترین نتایج، `REF_LOSS` را از چندین نمونه Ground Truth محاسبه کنید و/یا اندپوینت کالیبراسیون را اعمال کنید.

## ${\color{#8CE4FF}\textsf{نکات اضافی محاسبات}}$

- دکل‌های ماکرو (۲G/۳G/۴G/۵G) معمولاً حدود ۲۰ تا ۴۰ وات روی هر سکتور می‌فرستند که معادل تقریباً ۴۳ تا ۴۶ dBm روی هر حامل است و شبکه‌های ایران هم در همین محدوده کار می‌کنند.[^1][^2][^3]
- در فرمول فاصله، هم TX و هم RSRP باید بر حسب dBm باشند و REF_LOSS هم بر حسب dB باشد تا عبارت $TX - RSRP - REF\_LOSS$ از نظر واحدی درست باشد.[^6][^4][^5]
- برای یک دکل ماکرو شهری معمولی LTE/5G، مقدار پیش‌فرض مناسب TX ≈ ۴۳ dBm (حدود ۲۰ وات) است و برای سایت‌های قوی‌تر روستایی می‌توانی تا حدود ۴۶ dBm در نظر بگیری.[^2][^3][^1]
- در small cell / پیکوسل / in‑building توان TX معمولاً خیلی کمتر است (حدود ۳۰ تا ۳۷ dBm) و بهتر است عدد دیفالت را متناسب با آن پایین‌تر بگذاری.[^7][^1]
- برای شروعِ تست فرمول، می‌توانی TX = ۴۳ dBm، ضریب n بین ۲ تا ۳، و REF_LOSS برابر با تلفات مسیر در فاصلهٔ مرجع (مثلاً ۱ متر) انتخاب کنی.[^4][^5]


# ${\color{#FEEE91}\textsf{۳. پیاده‌سازی پایتون}}$

اسکریپت جامع ترکیب کننده تخمین سکتور، تصویرسازی هندسی، مرکز ثقل و مثلث‌بندی.

```
import math

class CellTower:
    def __init__(self, name, lat, lon, rsrp, cell_id=None, ta=None):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.rsrp = rsrp
        self.cell_id = cell_id
        self.ta = ta
        # Calculate approximate radius using Path Loss Model (n=3.5, TX=45)
        self.radius_km = math.pow(10, (45 - rsrp) / 35.0) / 1000.0

# --- Helper: Estimate Sector Direction ---
def get_sector_direction(cell_id):
    if not cell_id: return "Unknown"
    
    # Hybrid Rule (Multi-Band LTE support)
    local_id = int(cell_id) % 256  # Extract Local Cell ID
    sector_digit = local_id % 10   # Extract last digit (e.g. 11 -> 1)
    
    if sector_digit == 1: return 60   # North/NE Center
    elif sector_digit == 2: return 180 # South Center
    elif sector_digit == 3: return 300 # West Center
    
    return 0 # Default to North if unknown

# --- Algorithm 1: Geometric Projection (Single Tower) ---
def project_coordinates(lat, lon, distance_km, bearing_deg):
    """
    Calculates new Lat/Lon given a start point, distance, and bearing.
    Uses Haversine Destination Formula.
    """
    R = 6371.0 # Earth Radius in km
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg)
    
    # Calculate new latitude
    new_lat_rad = math.asin( math.sin(lat_rad) * math.cos(distance_km/R) +
                             math.cos(lat_rad) * math.sin(distance_km/R) * math.cos(bearing_rad) )
    
    # Calculate new longitude
    new_lon_rad = lon_rad + math.atan2( math.sin(bearing_rad) * math.sin(distance_km/R) * math.cos(lat_rad),
                                        math.cos(distance_km/R) - math.sin(lat_rad) * math.sin(new_lat_rad) )
    
    return math.degrees(new_lat_rad), math.degrees(new_lon_rad)

# --- Algorithm 2: Weighted Centroid ---
def calculate_weighted_centroid(towers):
    sum_lat, sum_lon, sum_weight = 0, 0, 0
    for t in towers:
        # Inverse weight: Stronger signal (smaller absolute value) -> Higher weight
        weight = 1.0 / abs(t.rsrp)
        sum_lat += t.lat * weight
        sum_lon += t.lon * weight
        sum_weight += weight
    return sum_lat / sum_weight, sum_lon / sum_weight

# --- Algorithm 3: Trilateration (Linearized) ---
def trilaterate(t1, t2, t3):
    x1, y1, r1 = t1.lat, t1.lon, t1.radius_km
    x2, y2, r2 = t2.lat, t2.lon, t2.radius_km
    x3, y3, r3 = t3.lat, t3.lon, t3.radius_km

    A = 2*x2 - 2*x1
    B = 2*y2 - 2*y1
    C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
    D = 2*x3 - 2*x2
    E = 2*y3 - 2*y2
    F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2

    det = (B*D) - (E*A)
    if det == 0: return None # Collinear error

    final_lat = ((C*E) - (F*B)) / ((E*A) - (B*D))
    final_lon = ((C*D) - (F*A)) / ((B*D) - (A*E))
    return final_lat, final_lon
```

# ${\color{#FFA239}\textsf{منابع (References) 📚}}$

1. **Rappaport, T. S.** (2002). _Wireless Communications: Principles and Practice_ (2nd ed.). Prentice Hall.
    
    - _Reference for Path Loss Models and urban attenuation factors (_$n$_)._
        
2. **3GPP TS 36.214**. _Evolved Universal Terrestrial Radio Access (E-UTRA); Physical layer; Measurements._
    
    - _Standard definitions for RSRP, RSRQ, and Cell ID decoding._
        
3. **3GPP TS 36.133**. _Requirements for support of radio resource management._
    
    - _Source for Timing Advance (TA) distance calculation standards._
        
4. **Balanis, C. A.** (2016). _Antenna Theory: Analysis and Design_ (4th ed.). Wiley.
    
    - _Explanation of Side Lobes and Back Lobes causing near-field direction errors._
        
5. **ITU-R Recommendation P.525-4**. Calculation of free-space attenuation. International Telecommunication Union (2019).
    
    - _Useful for the free-space path loss (FSPL) expression used to estimate REF_LOSS._
        
6. **Haversine formula — Wikipedia**. https://en.wikipedia.org/wiki/Haversine_formula
    
    - _Reference for the great-circle distance computation between two WGS84 coordinates._
        
7. **Trilateration — Wikipedia**. https://en.wikipedia.org/wiki/Trilateration
    
    - _Reference describing the algebraic formulation used for solving circle intersections in planar coordinates._
        
8. **Free-space path loss — Wikipedia**. https://en.wikipedia.org/wiki/Free-space_path_loss
    
    - _Background and derivation of the FSPL formula in dB used by the REF_LOSS estimator._
        
9. **OpenCellID Wiki**. _Public:CellID_. https://wiki.opencellid.org/wiki/Public:CellID
    
    - _Reference for Sector ID heuristics and numbering schemes (Part 3, Section 3)._
        
10. **Telcoma Global**. _What is the formula for Cell ID (ECI) in LTE networks?_ https://www.telcomaglobal.com/p/formula-cell-id-eci-lte-networks
    
    - _Reference for LTE ECI decomposition and Local Cell ID calculation (Part 3, Section 3)._
        
11. **Mozilla Ichnaea (GitHub)**. _Issue #415: 16-bit cellids with radio LTE._
    
    - _Reference confirming the "Last Digit Rule" on Local Cell IDs for multi-band networks (Part 3, Section 3C)._
        
12. **Movable Type Scripts**. _Calculate distance, bearing and more between Latitude/Longitude points._ https://www.movable-type.co.uk/scripts/latlong.html
    
    - _Source for the Destination Point formula (Geometric Projection) used in Single Tower scenarios._
        
13. **Shi, Q. et al.** (2014). _An Improved Weighted Centroid Localization Algorithm._ NADIA.
    
    - _Reference for the "Enhanced WCL" degree factor (_$g$_) improvement (Part 4, Scenario B)._
        
14. **Bourke, P.** (1997). _Intersection of two circles._
    
    - _Mathematical basis for the 2-tower geometric intersection logic (Part 4, Scenario B)._
        
15. **Blumenthal, J. et al.** (2007). _Weighted Centroid Localization in Zigbee-based Sensor Networks._ IEEE.
    
    - _Original formulation of the WCL weights (_$1/d^g$_) (Part 4, Scenario B)._
        
16. **Zhou, Y.** (2009). _An Efficient Least-Squares Trilateration Algorithm for Mobile Robot Localization._ IEEE IROS.
    
    - _Source for the Non-Linear Least Squares (NLLS) algorithm used in Scenario C._
        
17. **Gu, T. et al.** (2014). _B-Loc: Scalable Floor Localization Using Barometer on Smartphone._
    
    - _Reference for floor level estimation and barometric calibration strategies (Part 4, Scenario D)._
        
18. **Mozilla Ichnaea**. _Mozilla Location Service (MLS) Database Schema._
    
    - _Reference for standard cell measurement fields (Radio Type, Age, Specs) (Part 2, Section C)._
        
19. **OpenCellID**. _Database format and API._ https://wiki.opencellid.org/wiki/Database_format
    
    - _Reference for CSV column definitions (MCC, MNC, Radio, etc.) (Part 2, Section C)._
        

</div>
