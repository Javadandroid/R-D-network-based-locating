# Tower Cells Locating

![location](towers.jpg)

***Cellular Positioning*** Have 3 Methods that is a sub for ***Network-Based Positioning***
>1- **Cell ID (Coarse)** easiest way to find location that return cell tower location\
>2- **RSSI (Received Signal Strength Indicator)** Distance estimation based on ***signal strength***. The weaker the signal, the further the distance. (Moderate accuracy)\
>3- **TDOA / ToF (Time Difference of Arrival / Time of Flight)** Precise calculation of signal round-trip time between the phone and multiple towers for triangulation. (High accuracy and complex mathematics)

---

<br/><br/>

# Sending Data in diffrent Generations
# Generation 2 (GSM) Positioning Mechanics(BTS)

## Communication Mechanism (TDMA)
In GSM, synchronization is key to preventing signal collision in time slots.

* **Downlink (Tower -> Phone):** The BTS sends synchronization signals and the **Timing Advance (TA)** command.
* **Uplink (Phone -> Tower):** The Mobile Station (MS) sends an **Access Burst**. The tower measures the arrival time delay to calculate the distance.

## Key Positioning Parameters
1.  **CGI (Cell Global Identity):** Unique identifier for the serving cell (MCC-MNC-LAC-CID).
2.  **TA (Timing Advance):** The primary distance estimator.
    * *Range:* 0 to 63.
    * *Accuracy:* ~550 meters per unit (Low precision).
3.  **RXLEV (Received Signal Level):** Signal strength (measured in dBm) used for rough proximity estimation.
4.  **BSIC (Base Station Identity Code):** Distinguishes between neighboring cells using the same frequency.

<br/><br/>

# Generation 3 (UMTS/WCDMA) Positioning Mechanics(NodeB)

## Communication Mechanism (CDMA)
In 3G, all towers transmit on the same frequency simultaneously using unique codes.

* **The Challenge (Hearability):** Strong signals from the serving cell can drown out neighbor cells needed for triangulation (Near-Far problem).
* **Downlink (Tower -> Phone):** The network uses **IPDL (Idle Period Downlink)**. The serving NodeB briefly ceases transmission, creating a "silence period" that allows the User Equipment (UE) to detect weaker signals from neighbor cells via the **CPICH** (Common Pilot Channel).
* **Uplink (Phone -> Tower):** The UE measures the timing differences of these pilot signals and reports back to the network.

## Key Positioning Parameters
1.  **PSC (Primary Scrambling Code):** The unique identifier for the NodeB (tower) in the CDMA network.
2.  **RSCP (Received Signal Code Power):** The power of the specific pilot signal (CPICH) from a tower. This is the primary metric for path loss and distance estimation.
3.  **Ec/No (Energy per chip over Noise):** Represents the signal quality/interference ratio. Low Ec/No means high interference.
4.  **RTT (Round Trip Time):** Measures the time taken for a signal to travel to the tower and back, used for precise distance calculation (Successor to TA).

<br/><br/>

# Generation 4 (LTE) Positioning Mechanics(eNodeB)

## Communication Mechanism (OFDMA & PRS)
LTE utilizes an **OFDMA** structure, treating the frequency spectrum as a time-frequency grid.

* **Downlink (Tower -> Phone):** The network transmits dedicated **PRS (Positioning Reference Signals)**. These signals are staggered in the time-frequency grid so that PRS from neighboring cells do not interfere with each other, allowing the UE to detect multiple towers clearly.
* **Uplink/Measurement:** The UE measures the **RSTD (Reference Signal Time Difference)** between the serving cell and neighbor cells and reports it for calculation (OTDOA method).

## Key Positioning Parameters
1.  **PCI (Physical Cell ID):** The unique physical identifier for the cell (Range: 0-503).
2.  **RSRP (Reference Signal Received Power):** The linear average power of the reference signals. This is the **standard metric** for coverage and distance estimation in LTE, offering superior stability over legacy RSSI.
3.  **RSRQ (Reference Signal Received Quality):** Indicates the quality of the received signal, helpful for assessing interference.
4.  **TA (Timing Advance):** Highly refined distance measurement.
    * *Range:* 0 to 1282.
    * *Accuracy:* ~78 meters per unit (High precision).


<br/><br/>

# Generation 5 (5G NR) Positioning Mechanics(gNodeB)

## Communication Mechanism (Beamforming & Sweeping)
5G introduces a paradigm shift from omnidirectional broadcasting to directional **Beamforming**.

* **Downlink (Beam Sweeping):** The gNodeB (tower) transmits Synchronization Signal Blocks (SSB) in sequential beams covering different angular sectors (Beam Sweeping).
* **Uplink/Measurement:** The UE identifies the strongest beam (Best Beam) and reports its index (Beam ID) and signal quality back to the network. This provides the network with the user's **angular direction** relative to the tower.

## Key Positioning Parameters
1.  **Beam ID (SSB Index):** Identifies the specific spatial beam covering the user. This is the primary proxy for **Direction/Angle**.
2.  **SS-RSRP (Synchronization Signal RSRP):** The received power of the specific SSB beam (linear average).
3.  **AoA / AoD (Angle of Arrival / Departure):** Critical for geometric triangulation.
    * *AoA:* The angle at which the UE signal hits the tower antenna array.
    * *AoD:* The angle at which the tower transmits towards the UE.
4.  **PCI (Physical Cell ID):** Expanded range (0-1007) compared to LTE.



Mobile Country Codes (MCC) and Mobile Network Codes (MNC)

Raw JSON Data

بسیار عالی. این دیتای خامی که فرستادی (Raw JSON Data)، طلاست! این دقیقاً همون چیزیه که سیستم‌عامل اندروید از لایه‌های پایین سخت‌افزار مودم (Modem/Baseband) می‌گیره.

کلیدواژه‌های جستجو برای مقالات این بخش:

RSS-based Trilateration Algorithm

Path Loss Exponent Estimation in Urban Environments

Cellular Positioning utilizing Timing Advance (TA)

Weighted Least Squares for Localization

دیتای ورودی: همین JSON که داری.

Lookup: با استفاده از APIهایی مثل Mozilla Location Service، مختصات دکل‌هایی که CellID اون‌ها رو می‌بینی بگیر.

Distance Estimation:

برای LTE: استفاده از فرمول Log-Distance روی rsrp.

برای GSM: استفاده از mTa (Timing Advance).

Positioning Algorithm: استفاده از الگوریتم Weighted Least Squares (WLS). چرا Weighted؟ چون دکلی که سیگنال قوی‌تر داره (مثل اون LTE با -60) باید تاثیر بی

کلیدواژه‌های تخصصی برای سرچ مقالات 5G
اگر میخوای در این زمینه (5G Positioning) مقاله بخونی، باید دنبال این عبارت‌ها بگردی (چون با عبارات 4G فرق دارن):

5G NR Positioning: عبارت کلی برای مکان‌یابی در استاندارد جدید.

mmWave Localization / Positioning: مکان‌یابی با امواج میلی‌متری (دقت در حد سانتی‌متر!).

Beam Management / Beam Alignment: استفاده از پرتوها برای پیدا کردن جهت کاربر.

Hybrid AoA/ToF Positioning: ترکیب زاویه و زمان پرواز (دقیق‌ترین روش موجود).

PRS (Positioning Reference Signal): سیگنال‌های مخصوصی که در 5G فقط برای مکان‌یابی ارسال می‌شن و نویز دیتا رو ندارن.

https://github.com/gante/mmWave-localization-learning


Name	Required	Description
latitude	*	Latitude of data point in Decimal Degrees (ex. 49.231).
longitude	*	Longitude of data point in Decimal Degrees (ex. -123.1232).
altitude	*	Altitude, in metres
MCC	*	Mobile Country Code
MNC	*	Mobile Network Code
LAC	*	Location Area Code / Tracking Area Code (TAC)
CID	*	Full Cell ID / Cell Identifier (CI, not CGI for LTE)
Signal	*	RSSI Signal strength in dBm / RSRP for LTE
type	*	one of: GSM,UMTS,CDMA, or LTE
subtype	*	for GSM above: GPRS, EDGE
for UMTS above: UMTS, HSDPA, HSUPA, HSPA, HSPA+, DC-HSPA+

for LTE above: LTE, LTE-A

for CDMA above: CDMA, 1xRTT, EVDO, EHRPD

ARFCN		Number representing 3GPP ARFCN/EARFCN/UARFCN (frequency)
PSC or PCI		UMTS Primary Scrambling Code or LTE Physical Cell Identity


Neighbor cells
AT+CCED=0,2

The report is in the following format:

+CCED:LTE neighbor cell:<MCC>,<MNC>,<frequency>,<cellid>,<rsrp>,<rsrq>,<tac>,<SrxLev>,<pcid>

+CCED:GSM neighbor cellinfo:<MCC>,<MNC>,<lac>,<cellid>,<bsic>,<rxlev>