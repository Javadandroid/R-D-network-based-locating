# ${\color{#FF5656}\textsf{Cell Towers Locating}}$

_**Cellular Positioning**_ generally relies on 3 core methods, acting as a substitute for Network-Based Positioning:

> 1. **Cell ID (Coarse):** The simplest method. Returns the location of the serving cell tower. (Low accuracy)
>     
> 2. **RSSI / RSRP (Signal Strength):** Distance estimation based on signal power. The weaker the signal, the further the distance. (Moderate accuracy)
>     
> 3. **TDoA / ToF (Time Difference of Arrival):** Precise calculation of signal round-trip time between the phone and multiple towers for triangulation. (High accuracy, complex mathematics)
>     

# ${\color{#FFA239}\textsf{Part 1: Network Evolution \\& Mechanics}}$

Understanding how different generations communicate is vital for selecting the right positioning parameters.

# ${\color{#FEEE91}\textsf{1. Generation 2 (GSM) Positioning Mechanics (BTS)}}$

## ${\color{#8CE4FF}\textsf{Communication Mechanism (TDMA)}}$

In GSM, synchronization is key to preventing signal collision in time slots.

- **Downlink (Tower -> Phone):** The BTS sends synchronization signals and the **Timing Advance (TA)** command.
    
- **Uplink (Phone -> Tower):** The Mobile Station (MS) sends an **Access Burst**. The tower measures the arrival time delay to calculate the distance.
    

## ${\color{#8CE4FF}\textsf{Key Parameters}}$

1. **CGI (Cell Global Identity):** Unique identifier (MCC-MNC-LAC-CID).
    
2. **TA (Timing Advance):** Range 0-63. Accuracy ~550m per unit (Low precision).
    
3. **RXLEV:** Received Signal Level (dBm).
    
4. **BSIC:** Base Station Identity Code (distinguishes neighboring cells).
    

# ${\color{#FEEE91}\textsf{2. Generation 3 (UMTS/WCDMA) Positioning Mechanics (NodeB)}}$

## ${\color{#8CE4FF}\textsf{Communication Mechanism (CDMA)}}$

All towers transmit on the same frequency simultaneously using unique codes.

- **The Challenge (Hearability):** Strong signals from the serving cell can drown out neighbors (Near-Far problem).
    
- **Solution (IPDL):** The network uses **Idle Period Downlink**. The serving NodeB briefly ceases transmission, allowing the UE to detect weaker neighbor signals via **CPICH** (Common Pilot Channel).
    

## ${\color{#8CE4FF}\textsf{Key Parameters}}$

1. **PSC (Primary Scrambling Code):** Unique identifier for the NodeB.
    
2. **RSCP (Received Signal Code Power):** Power of the CPICH pilot signal. Primary metric for path loss.
    
3. **RTT (Round Trip Time):** Successor to TA for distance calculation.
    

# ${\color{#FEEE91}\textsf{3. Generation 4 (LTE) Positioning Mechanics (eNodeB)}}$

## ${\color{#8CE4FF}\textsf{Communication Mechanism (OFDMA \\& PRS)}}$

LTE treats the frequency spectrum as a time-frequency grid.

- **Downlink:** The network transmits dedicated **PRS (Positioning Reference Signals)**. These are staggered to prevent interference, allowing clear detection of multiple towers.
    
- **Uplink:** The UE measures **RSTD (Reference Signal Time Difference)** for OTDOA calculation.
    

## ${\color{#8CE4FF}\textsf{Key Parameters}}$

1. **PCI (Physical Cell ID):** Unique physical ID (Range: 0-503).
    
2. **RSRP (Reference Signal Received Power):** Linear average power of reference signals. More stable than RSSI.
    
3. **TA (Timing Advance):** Range 0-1282. Accuracy **~78 meters** per unit (High precision).
    

# ${\color{#FEEE91}\textsf{4. Generation 5 (5G NR) Positioning Mechanics (gNodeB)}}$

## ${\color{#8CE4FF}\textsf{Communication Mechanism (Beamforming)}}$

5G shifts from omnidirectional broadcasting to directional **Beamforming**.

- **Downlink:** The gNodeB transmits Synchronization Signal Blocks (SSB) in sequential beams (Beam Sweeping).
    
- **Measurement:** The UE identifies the **Best Beam** index, providing the network with the user's **angular direction**.
    

## ${\color{#8CE4FF}\textsf{Key Parameters}}$

1. **Beam ID (SSB Index):** Primary proxy for **Direction/Angle**.
    
2. **SS-RSRP:** Received power of the specific SSB beam.
    
3. **AoA / AoD:** Angle of Arrival / Departure (Critical for geometric triangulation).
    
4. **Note on Data:** Open data for 5G is scarce; "4G Fallback" is often used for positioning.
    

# ${\color{#FFA239}\textsf{Part 2: Data Acquisition}}$

To locate a user, we first need to identify the visible towers and map them to physical coordinates.

# ${\color{#FEEE91}\textsf{Decoding Signals (What the Phone Sees)}}$

Telecommunication towers broadcast **System Information Blocks (SIB)**. Even without a SIM card, a device can decode:

## ${\color{#8CE4FF}\textsf{A) Identity Parameters (The Address)}}$

- **MCC:** Mobile Country Code (e.g., 432 for Iran).
    
- **MNC:** Mobile Network Code (e.g., 11 for MCI).
    
- **LAC/TAC:** Location/Tracking Area Code.
    
- **CID/ECI:** Unique Cell Identity.
    

## ${\color{#8CE4FF}\textsf{B) Signal \\& Timing}}$

- **RSSI/RSRP:** How "loud" the tower is (Distance proxy).
    
- **TA/ToA:** Signal delay (Time-based distance proxy).
    

# ${\color{#FEEE91}\textsf{Data Sources (Mapping ID to Coordinates)}}$

Since towers don't broadcast their Lat/Lon, we use external databases.

## ${\color{#8CE4FF}\textsf{A) Open Source Databases}}$

- **OpenCellID:** Largest open database. Good for 2G/3G/4G. Weak on 5G.
    
- **Mozilla Location Service (MLS):** _Retired (2024)._ No longer a viable source.
    

## ${\color{#8CE4FF}\textsf{B) Commercial APIs}}$

- **Google Geolocation API / Unwired Labs:** High accuracy, supports 5G, paid services.
    

## ${\color{#8CE4FF}\textsf{C) "War Driving" (Manual Collection)}}$

For private networks or high-precision needs (e.g., specific campuses), you must build your own database. To ensure data quality and post-processing capability, the schema must be robust.

- **Method:** Drive/walk with a logger app recording **Cell ID + GPS**.
    
- **The "Golden Data List" to Log (Database Schema):**
    
    1. **Radio Type:** Critical for determining which standard (GSM/LTE/5G) applies.
        
    2. **Identifiers:** MCC, MNC, LAC/TAC, CID/ECI.
        
    3. **Physical ID:** PCI (LTE/5G) or PSC (UMTS). Vital for resolving neighbor cells where CID is not decoded.
        
    4. **Signal Strength:** RSRP (dBm) for LTE, RSSI for Legacy.
        
    5. **Signal Quality:** RSRQ/SNR. Helps filter out "noisy" measurements that shouldn't be used for triangulation.
        
    6. **Timing Advance (TA):** If available, provides direct distance range (0-1282).
        
    7. **GPS Location:** Latitude, Longitude, Altitude (for 3D fixes).
        
    8. **GPS Accuracy:** Discard if $> 20m$.
        
    9. **Speed & Bearing:** Helps correct for Doppler shift or filter out measurements taken while moving too fast (unstable handover).
        
    10. **Device Info:** Model & OS Version. Different chips report signal strength differently; this allows for calibration.
        

**Django Model Implementation:**

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

# ${\color{#FFA239}\textsf{Part 3: Technical Challenges \\& Pre-Processing}}$

Before running algorithms, raw modem data must be sanitized. Android APIs (`getAllCellInfo`) often return artifacts that cause massive errors.

# ${\color{#FEEE91}\textsf{1. The "Ghost Cell" Phenomenon 👻}}$

Modems prioritize battery life. They monitor the **Physical Layer** of neighbor cells (signal strength) but often skip decoding the **Data Layer** (Identity).

- **Symptom:** You get `RSRP` and `PCI`, but `MNC` or `CID` are invalid.
    
- **Solution:**
    
    - _Basic:_ Filter out these cells.
        
    - _Advanced:_ Use PCI matching if you have a high-definition database.
        

# ${\color{#FEEE91}\textsf{2. Sentinel Values (Data Artifacts) 🐞}}$

When the modem fails to read a value, it returns specific "Max Values". These must be filtered out.

| **Parameter** | **Invalid Value** | **Reason** | | **MCC/MNC** | `2147483647` | `Integer.MAX_VALUE` (Identity not decoded) | | **TAC** | `65535` | 16-bit Overflow (`0xFFFF`) | | **CI** | `268435455` | 28-bit Max Value |

**Filtering Logic (Pseudo-code):**

```
if (cell.mcc == Int.MAX_VALUE || cell.ci == Int.MAX_VALUE) {
    continue; // Skip Ghost Cell
}
```

# ${\color{#FEEE91}\textsf{3. The Directionality Problem (Sectorization) 🍕}}$

Towers are not omnidirectional. They are usually divided into 3 sectors (120° each). Since Azimuth is rarely public, we use heuristics to guess the direction based on the **Cell ID structure**:

**A) The "Last Digit" Rule (GSM/UMTS/Legacy)** Common in older networks or specific vendors (e.g., Huawei/Ericsson standard configs).

- **Ends in 1 (or 0):** Sector 1 $\rightarrow$ North/NE ($0^\circ-120^\circ$)
    
- **Ends in 2 (or 1):** Sector 2 $\rightarrow$ South-East ($120^\circ-240^\circ$)
    
- **Ends in 3 (or 2):** Sector 3 $\rightarrow$ West ($240^\circ-360^\circ$)
    

**B) The Modulo-256 Rule (LTE/5G)** In LTE, the 28-bit ECI (E-UTRAN Cell Identity) is a combination of the eNodeB ID and a Local Cell ID.

- **Formula:** $\text{Local Cell ID} = \text{ECI} \pmod{256}$
    
- **Interpretation:**
    
    - **0, 1, 2:** Often correspond to Sectors 1, 2, 3 (Primary Band).
        

**C) The "Hybrid" Rule (Multi-Band LTE)** Used when operators "stack" bands using offsets in the Local Cell ID (e.g., Band A=1-3, Band B=11-13, Band C=21-23).

- **Logic:** First, isolate the Local ID (`ECI % 256`). Then, extract the last digit (modulo 10) to strip the band offset.
    
- **Why?** A Local ID of `11` means "Sector 1, Band 2". The `1` (from 11) indicates direction.
    
- **Python Implementation:**
    
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
    

# ${\color{#FFA239}\textsf{Part 4: Positioning Algorithms}}$

Once data is cleaned, we select an algorithm based on the number of visible towers.

# ${\color{#FEEE91}\textsf{Scenario A: Single Tower (Geometric Sector Projection)}}$

**Condition:** Only 1 valid tower is visible. **Logic:** Instead of assuming the user is _at_ the tower, we project their location away from the tower based on the estimated distance and the sector's "Bisector Angle" (Azimuth) .

1. **Look up:** Tower Lat/Lon.
    
2. **Estimate Distance (**$d$**):** Use Timing Advance (TA) or Path Loss.
    
3. **Determine Azimuth (**$\theta$**):** Use the sector heuristic to find the center angle of the beam.
    
    - Sector 1: $\approx 60^\circ$
        
    - Sector 2: $\approx 180^\circ$
        
    - Sector 3: $\approx 300^\circ$
        
4. **Geometric Projection:** Calculate the new coordinates $(lat_{new}, lon_{new})$ by moving distance $d$ along angle $\theta$ from the tower.
    
    - _Note:_ This places the user in the "center of gravity" of the sector slice, reducing the maximum error compared to the tower location.
        

# ${\color{#FEEE91}\textsf{Scenario B: Two Towers (Weighted Centroid \\& Geometric Intersection)}}$

**Condition:** 2 distinct anchors (e.g., Dual SIM or Serving + 1 Strong Neighbor). With only two reference points, standard triangulation is impossible (infinite solutions). We use one of two methods:

**Method 1: Enhanced Weighted Centroid (Fast)** Instead of placing the user on the straight line between towers, we pull the location exponentially closer to the stronger signal using a degree factor ($g$).

- **Formula:**
    
    $$Lat_{user} = \frac{\sum (Lat_i \cdot w_i)}{\sum w_i}$$
- **Weight (**$w_i$**):** $w_i = \frac{1}{(d_i)^g}$
    
    - Where $d_i$ is the estimated distance.
        
    - $g$ is the degree factor (Typically $g \approx 1-2$ for Centroid).
        

**Method 2: Geometric Intersection (Precise)** Two circles intersect at **two points**. We can calculate both and discard the invalid one using Sector Logic.

1. **Calculate Intersection Points:** Find the two points where the radius circles ($r_1, r_2$) cross.
    
2. **Filter by Sector:** Check which point lies within the "Cone of Visibility" (Sector Azimuth) of the towers.
    

**Python Implementation (Circle Intersection):**

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

# ${\color{#FEEE91}\textsf{Scenario C: Three+ Towers (Advanced Trilateration)}}$

**Condition:** 3 or more resolved anchors. **Logic:** Finding the intersection of multiple circles. In the real world, measurements are noisy, so circles rarely intersect perfectly at one point. We must minimize the error.

**Method 1: Linearized System (Basic)** Subtracts equations to remove quadratic terms. Fast but sensitive to noise.

- **Math:** $A \cdot x + B \cdot y = C$
    

**Method 2: Non-Linear Least Squares (Pro)** Uses iterative optimization (like Levenberg-Marquardt) to find the $(x, y)$ that minimizes the sum of squared errors between measured and calculated distances.

- **Formula to Minimize:**
    
    $$S = \sum_{i=1}^{n} (\sqrt{(x-x_i)^2 + (y-y_i)^2} - d_i)^2$$

**Python Implementation (NLLS with Scipy):**

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

# ${\color{#FEEE91}\textsf{Scenario D: The High-Rise Challenge (Barometric Altimetry) 🏢}}$

**Problem:** In skyscrapers, the phone connects to distant LoS towers. Standard 2D algorithms fail because the **Slant Range** (hypotenuse) is significantly longer than the **Ground Distance** (horizontal leg). **Fix:** Use the device's Barometer to calculate altitude ($z$) and correct the distance.

**Step 1: Calculate Altitude (Barometric Formula)** Using the international barometric formula to estimate height above sea level or relative to the ground floor.

$$h = 44330 \cdot \left(1 - \left(\frac{P}{P_0}\right)^{\frac{1}{5.255}}\right)$$

- $P$: Measured Pressure (hPa).
    
- $P_0$: Reference Pressure (Sea level or Ground floor).
    

**Step 2: 3D to 2D Correction (Slant Range)** Convert the measured radius (hypotenuse) to ground radius (leg) for accurate map plotting.

$$d_{ground} = \sqrt{d_{slant}^2 - (h_{tower} - h_{user})^2}$$

**Python Implementation (Altitude & Floor):**

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

# ${\color{#FFA239}\textsf{Part 5: Mathematical Models \\& Implementation}}$

# ${\color{#FEEE91}\textsf{1. Physics: Calibration \\& Path Loss}}$

To convert Signal Strength (RSRP) to Distance ($d$), we use the Log-Distance Path Loss Model.

## ${\color{#8CE4FF}\textsf{The Formula}}$

$$d = 10^{\frac{(TX - RSRP) - REF\_LOSS}{10 \cdot n}}$$

- **TX:** Tower transmission power (Default $\approx 40-45$ dBm).
    
- **RSRP:** Measured signal at user.
    
- **REF_LOSS:** Loss at 1 meter. Calculated as: $20 \log_{10}(f_{MHz}) + 32.44 - G_t - G_r$.
    
- **n (Exponent):** Environment factor.
    
    - Free Space: 2.0
        
    - Urban: 3.5 - 4.0
        

## ${\color{#8CE4FF}\textsf{Calibration (Finding 'n')}}$

If you have a ground truth (GPS) and a signal reading, you can reverse the formula to find the effective $n$ for your area:

$$n_{effective} = \frac{(TX - RSRP) - REF\_LOSS}{10 \cdot \log_{10}(d_{GPS})}$$

# ${\color{#FEEE91}\textsf{2. REF\\_LOSS Estimator Details (Reference Path Loss at 1m)}}$

**Purpose:** Produce a reasonable `REF_LOSS` (dB) value when the per-site constant is unknown. This value represents the expected free-space loss (plus small system losses) at a reference distance of 1 meter and is used as the additive constant in the path-loss model.

## ${\color{#8CE4FF}\textsf{Approach Implemented}}$

1. **Convert Frequency:** Convert `earfcn` (if provided) to downlink frequency in MHz using a band table.
    
2. **Compute FSPL at 1m:** The estimator follows the free-space path-loss (FSPL) expression in dB:
    

$$\mathrm{FSPL}_{1\mathrm{m}} = 20\,\log_{10}(f_{\mathrm{MHz}}) + 32.44$$

3. **Adjust for Gains & Losses:** The project adjusts FSPL by antenna gains and system losses to produce the reference loss constant:
    

$$\mathrm{REF\_LOSS} = \mathrm{FSPL}_{1\mathrm{m}} - G_t - G_r + L_{\mathrm{sys}}$$

- $G_t$: Transmitter antenna gain (dBi).
    
- $G_r$: Receiver antenna gain (dBi).
    
- $L_{\mathrm{sys}}$: Combined system/cable loss (dB).


## ${\color{#8CE4FF}\textsf{Additional Notes About Calculation}}$

- Macro cell sites (2G/3G/4G/5G) usually transmit about 20–40 W per sector, which is roughly 43–46 dBm per carrier, and Iranian operators are in the same range as global networks.
- In your distance formula, TX and RSRP must both be in dBm, and REF_LOSS must be in dB so that the subtraction $TX - RSRP - REF\_LOSS$ is meaningful.
- A practical default for a typical urban macro LTE/5G site is TX ≈ 43 dBm (about 20 W), and for stronger rural/long-range macros you can assume up to about 46 dBm.
- For small cells / pico / indoor nodes, real TX is lower (around 30–37 dBm), so your default should be reduced accordingly.
- For testing your formula, you can start with TX = 43 dBm, n between 2 and 3, and REF_LOSS equal to the path loss at a reference distance (for example 1 meter).

# ${\color{#FEEE91}\textsf{3. Python Implementation}}$

Comprehensive script combining Sector Estimation, Geometric Projection, Centroid, and Trilateration.

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

# ${\color{#FFA239}\textsf{References 📚}}$

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
