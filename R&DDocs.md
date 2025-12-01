# Tower Cells Locating

![location](towers.jpg)

***Cellular Positioning*** Have 3 Methods that is a sub for ***Network-Based Positioning***
>1- **Cell ID (Coarse)** easiest way to find location that return cell tower location\
>2- **RSSI (Received Signal Strength Indicator)** Distance estimation based on ***signal strength***. The weaker the signal, the further the distance. (Moderate accuracy)\
>3- **TDOA / ToF (Time Difference of Arrival / Time of Flight)** Precise calculation of signal round-trip time between the phone and multiple towers for triangulation. (High accuracy and complex mathematics)

---

<br/><br/>

# Sending Data in diffrent Generations
# 1. Generation 2 (GSM) Positioning Mechanics(BTS)

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

# 2. Generation 3 (UMTS/WCDMA) Positioning Mechanics(NodeB)

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

$${\color{red}Welcome
# 3. Generation 4 (LTE) Positioning Mechanics(eNodeB)
}


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

# 4. Generation 5 (5G NR) Positioning Mechanics(gNodeB)

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

<br/><br/>

# Locating Towers
Telecommunication towers (BTS/NodeB/eNodeB/gNodeB) continuously broadcast data packages known as **"System Information Blocks" (SIB)** into the air. A user's device can "hear" and decode these signals even without an active SIM card.

This information includes three categories vital for positioning:

### A) Identity Parameters
These act as the "postal address" of the tower. Combining these numbers creates a **Cell Global Identity (CGI)**:

* **MCC (Mobile Country Code):** Country code (e.g., 432 for Iran).
* **MNC (Mobile Network Code):** Operator code (e.g., 11 for MCI, 35 for Irancell).
* **LAC/TAC (Location/Tracking Area Code):** Area code (similar to a neighborhood zip code).
* **CID/ECI (Cell Identity):** The unique ID (specific plate number) of that specific antenna.

### B) Signal Strength
The phone measures how "loud" or "quiet" the tower sounds.

* **RSSI (2G/3G):** Total Received Signal Strength Indicator.
* **RSRP (4G/5G):** Reference Signal Received Power. This is more precise and stable than RSSI, measuring only the reference signal power.

### C) Timing Parameters
* **TA (Timing Advance):** A value sent by the tower to the phone to compensate for transmission delay (directly related to distance).
* **ToA (Time of Arrival):** The exact arrival time of the signal (highly precise in 4G and 5G networks).


## Where to Find Tower Coordinates? (Data Sources)

Since cell towers do not broadcast their own geographic coordinates (Latitude/Longitude), we must rely on external databases to map a Cell ID to a physical location.

### A) Open Source Databases 🌐
These databases are crowdsourced by users. You can download the entire dataset for free.
* **OpenCellID:** The world's largest open community database of cell towers.
    * *Pros:* Free, extensive coverage for 2G, 3G, and 4G (LTE).
    * *Cons:* **Weak 5G coverage.** Since 5G requires specialized hardware/software to log accurate Beam IDs, user contributions are scarce.
* **Mozilla Location Service (MLS):**
    * *Status:* **Retired (2024).** While it was a major source, it is no longer accepting new data, making it unsuitable for future-proof applications.

### B) Commercial APIs 💼
Tech giants collect massive amounts of data from Android/iOS devices to build highly accurate, proprietary maps.
* **Google Geolocation API / Unwired Labs:**
    * *Pros:* Extremely accurate, supports 5G, and updates in real-time.
    * *Cons:* Paid services (usually with a limited free tier). Best for commercial or high-precision needs.

    Example of unwiredlabs:
    ![unwired lab](unwiredlabs.png)

### C) "War Driving" (Manual Collection) 🚗
For specific, local projects (e.g., a university campus or industrial site), you can build your own database.
* *Method:* Drive or walk through the target area with a customized app that logs the **Cell ID** and your phone's **GPS coordinates** simultaneously.
* *Use Case:* Essential when working with private networks or areas where open data is missing.

### 💡 Strategy for 5G Positioning
Due to the lack of open 5G data, a common workaround is **"4G Fallback"**. Since most current 5G networks (NSA) rely on a 4G anchor, you can use the coordinate of the associated 4G tower to estimate the user's general location.

<br/><br/>

## Positioning Algorithms (Processing)

Once the device gathers data from nearby towers, specific algorithms are used to estimate the user's coordinates $(x, y)$.

### A) Proximity (Cell-ID Method) 📍
The simplest approach. It assumes the user is located at the exact coordinates of the serving cell tower.
* **Algorithm:** Query the database with the `Cell ID` -> Return Tower Lat/Long.
* **Accuracy:** Low. Defined by the cell's coverage radius (500m - several km).

### B) Trilateration (RSSI/RSRP Based) 📐
Uses signal strength to estimate distance from at least three towers.
* **Concept:** Intersection of three circles.
* **Formula (Path Loss Model):** Converts signal strength to distance ($d$).
    $$d = d_0 \cdot 10^{\frac{TX - RSRP}{10n}}$$
    * $TX$: Tower transmission power.
    * $n$: Path loss exponent (depends on environment, e.g., Urban = 3.5).
* **Challenge:** Signal reflection (Multipath) can cause huge errors in distance estimation.

### C) Multilateration (TDoA) ⏱️
Uses the *Time Difference of Arrival* of signals from multiple synchronized towers.
* **Concept:** Intersection of hyperbolas.
* **Mechanism:** If a signal from Tower A arrives $1\mu s$ before Tower B, the user is located on a specific hyperbolic curve relative to them.
* **Accuracy:** High, but requires precise nanosecond-level synchronization between towers.