# گزارش فنی: چالش‌ها و محدودیت‌های موقعیت‌یابی مخابراتی

# Technical Report: Challenges and Limitations of Mobile Network Positioning

## بخش اول: متن ویرایش شده (فارسی) | Part 1: Refined Text (Persian)

### ۱. محدودیت در تعداد دکل‌های در دسترس

در دستگاه‌های کاربر (مانند گوشی‌های هوشمند)، دسترسی به اطلاعات دکل‌ها بسیار محدود است. در صورت استفاده از گوشی‌های دو سیم‌کارت، حداکثر اطلاعات دو دکل و در گوشی‌های تک سیم‌کارت تنها اطلاعات یک دکل (Serving Cell) قابل استخراج است. این محدودیت باعث می‌شود ضریب خطای محاسباتی در حالت عادی تا حدود ۱۰۰۰ متر افزایش یابد.

### ۲. متدهای اندازه‌گیری فاصله

- **Timing Advance (TA):** این پارامتر اولویت اول در محاسبات است (به‌ویژه در نسل 4/LTE). دقت این پارامتر حدود ۷۸ متر به ازای هر واحد است (مثلاً TA=2 معادل فاصله تقریبی ۱۵۶ متر است).
    
- **RSRP و سیگنالینگ:** در صورت عدم دسترسی به TA یا اورفلو شدن آن، از پارامتر RSRP استفاده می‌شود. این روش به دلیل وابستگی به متغیرهایی نظیر توان خروجی دکل (Tx Power) و ضریب نفوذ محیطی (n effective) که در نقاط مختلف شهر و با توجه به موانع تغییر می‌کنند، دقت بسیار پایین‌تری دارد.
    

### ۳. ناهمگونی سخت‌افزاری و نرم‌افزاری

پارامترهای دریافتی بسته به مدل دستگاه و نسخه سیستم‌عامل متفاوت است. برخی دستگاه‌ها پارامترهای دقیق‌تری ارائه می‌دهند و برخی دیگر خیر. این موضوع پیاده‌سازی یک الگوریتم واحد را برای تمامی نسل‌های موبایل و برندها با چالش جدی مواجه می‌کند.

### ۴. جهت‌یابی و سکتوربندی (Directionality)

استفاده از CID برای تشخیص جهت سکتور (پوشش ۱۲۰ درجه‌ای) همواره دقیق نیست. در تست‌های عملیاتی، جهت پیش‌بینی شده گاهی کاملاً اشتباه یا حتی ۱۸۰ درجه معکوس گزارش می‌شود که نشان‌دهنده عدم انطباق داده‌های تئوریک با داکیومنت‌های فنی دکل‌ها در دنیای واقعی است.

### ۵. عدم دسترسی به دکل‌های همسایه (Neighbor Cells)

گوشی‌های عادی تا زمانی که به یک دکل متصل نشوند، پارامترهای حیاتی دکل‌های همسایه را دریافت نمی‌کنند. این موضوع امکان استفاده از روش‌هایی مانند Triangulation (سه‌ضلعی) را از بین می‌برد. همچنین مشکل "اورفلو" شدن مقادیر در لایه‌های نرم‌افزاری باعث بازگشت اعداد نامعتبر و خطا در محاسبات نهایی می‌شود.

## Part 2: English Translation

### 1. Limited Cell Tower Connectivity

On standard mobile devices, access is typically limited to the serving towers. Dual-SIM devices can provide data from up to two towers, while single-SIM devices are restricted to one. This lack of data points results in a high margin of error, often exceeding 1,000 meters.

### 2. Distance Measurement Methods

- **Timing Advance (TA):** This is the primary parameter, especially in 4G/LTE networks. It offers a precision of approximately 78 meters per unit (e.g., TA=2 corresponds to ~156 meters).
    
- **RSRP & Signal Metrics:** When TA is unavailable or overflows, the system falls back to RSRP. This method relies on variables such as `Tx Power` and `n-effective` (Path Loss Exponent). Since these vary based on urban obstacles and tower types, the resulting accuracy is significantly lower.
    

### 3. Device and Generation Variability

Received parameters vary significantly across different hardware and mobile generations. Some devices report comprehensive data, while others omit key metrics. This necessitates complex, device-specific programming logic to handle different data sets.

### 4. Sector Directionality Challenges

Determining signal direction via Cell ID (CID) often fails in field tests. While documentation suggests a 120-degree sector coverage, practical results frequently show incorrect or even 180-degree inverted directions.

### 5. Neighbor Cell Inaccessibility & Data Integrity

Standard mobile devices do not retrieve detailed parameters from neighboring cells unless a handover occurs. This prevents the use of triangulation techniques. Furthermore, software "overflow" issues often lead to corrupted or invalid data, further complicating position estimation.

## بخش سوم: راهکارها و پیشنهادها | Part 3: Solutions & Recommendations

برای بهبود دقت در شرایطی که محدودیت‌های فوق وجود دارد، راهکارهای زیر پیشنهاد می‌شود:

1. **Hybrid Positioning (موقعیت‌یابی ترکیبی):**
    
    - به جای اتکای صرف به دکل، از **Wi-Fi Scanning** استفاده کنید. دیتابیس‌های BSSID (مک‌آدرس مودم‌ها) بسیار دقیق‌تر از دکل‌های مخابراتی هستند و در محیط‌های شهری خطایی زیر ۳۰-۵۰ متر دارند.
        
    - استفاده از سنسورهای داخلی گوشی (Magnetometer و Accelerometer) برای تشخیص جهت حرکت و اصلاح خطای سکتوربندی.
        
2. **Fingerprinting Method (روش انگشت‌نگاری سیگنال):**
    
    - به جای فرمول‌های ریاضی (که به `n effective` وابسته هستند)، یک دیتابیس از قدرت سیگنال در نقاط مختلف شهر تهیه کنید. دستگاه با مقایسه سیگنال فعلی با الگوهای ذخیره شده، موقعیت را حدس می‌زند.
        
3. **استفاده از APIهای کمکی:**
    
    - استفاده از سرویس‌هایی مثل **Google Geolocation API** یا **Mozilla Location Service**. این سرویس‌ها اطلاعات دکل‌های همسایه و وای‌فای را به صورت جمع‌سپاری (Crowdsourced) دارند و خروجی بسیار دقیق‌تری نسبت به محاسبات خام TA/RSRP می‌دهند.
        
4. **فیلترینگ و حذف نویز (Kalman Filter):**
    
    - پیاده‌سازی فیلتر کالمن برای حذف پرش‌های ناگهانی (Outliers) ناشی از اورفلو شدن داده‌ها یا بازتاب سیگنال از ساختمان‌ها.
        
5. **Data Cleaning (پاکسازی داده):**
    
    - ایجاد یک لایه اعتبارسنجی که مقادیر غیرمنطقی (مانند فاصله منفی یا TA بسیار بالا) را قبل از ورود به الگوریتم حذف کند.