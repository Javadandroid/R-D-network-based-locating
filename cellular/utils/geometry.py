import math
from django.conf import settings


def _get_path_loss_params(tx_power, n, ref_loss):
    cfg = getattr(settings, 'PATH_LOSS', {})
    return (
        tx_power if tx_power is not None else cfg.get('TX_DEFAULT', 40),
        n if n is not None else cfg.get('N_DEFAULT', 5.2),
        ref_loss if ref_loss is not None else cfg.get('REF_LOSS', 80),
    )


def calculate_distance(rsrp, tx_power=None, n=None, ref_loss=None):
    """
    محاسبه فاصله با فرمول Path Loss
    
    فرمول: Path Loss = TX - RX = 10*n*log10(d) + C
    پس: d = 10^((TX - RX - C) / (10*n))
    
    برای تهران (Urban):
    - TX: 40 dBm (پیش‌فرض)
    - n: 3.5-4.0 (منطقه شهری)
    - C: ~70-85 (ثابت محیط)
    """
    if rsrp is None:
        return 500.0

    rsrp = -abs(rsrp)

    tx_power, n, ref_loss = _get_path_loss_params(tx_power, n, ref_loss)

    try:
        path_loss = tx_power - rsrp
        # d = 10^((PL - REF_LOSS) / (10*n))
        distance = math.pow(10, (path_loss - ref_loss) / (10 * n))
        # limit to sensible [10m, 50000m]
        distance = max(10.0, min(distance, 50000.0))
        return distance
    except Exception:
        return 500.0


def distance_from_ta(ta):
    """Approximate distance from LTE Timing Advance (TA). TA units ~78 meters.
    Accepts integer TA (0..1282) and returns meters. If ta is None or invalid, returns None.
    """
    if ta is None:
        return None
    try:
        ta_int = int(ta)
    except Exception:
        return None
    if ta_int < 0 or ta_int > 10000:
        return None
    return ta_int * 78.0


def earfcn_to_freq_mhz(earfcn):
    """Convert common LTE EARFCN (N_DL) to downlink frequency in MHz.
    Handles two cases:
    - If `earfcn` looks like a direct frequency (e.g., 1800 or 425), returns as MHz.
    - Otherwise, tries to map using common LTE band offsets (B1,B3,B7,B8,B20).
    Returns frequency in MHz or None if unknown.
    """
    if earfcn is None:
        return None
    try:
        n = int(earfcn)
    except Exception:
        return None

    # Heuristic: if value is in typical MHz range, assume it's already MHz
    if 70 <= n <= 6000:
        # common case where caller already provided freq in MHz (e.g., 1800)
        return float(n)

    # Standard mapping for common LTE bands (N_offs and F_DL_low)
    bands = [
        # name, n_offs, n_low, n_high, f_dl_low
        ("B1", 0, 0, 599, 2110.0),
        ("B3", 1200, 1200, 1949, 1805.0),
        ("B7", 2750, 2750, 3449, 2620.0),
        ("B8", 3450, 3450, 3799, 925.0),
        ("B20", 6150, 6150, 6449, 791.0),
    ]

    for name, n_offs, n_low, n_high, f_low in bands:
        if n_low <= n <= n_high:
            # F_DL = F_DL_low + 0.1 * (N - N_offs)
            return f_low + 0.1 * (n - n_offs)

    return None


def estimate_ref_loss_from_earfcn(earfcn, gt_dbi=15.0, gr_dbi=0.0, system_losses_db=3.0):
    """Estimate REF_LOSS (dB) using EARFCN -> frequency (MHz) then FSPL@1m.
    Returns REF_LOSS in dB or None if frequency cannot be determined.
    """
    freq = earfcn_to_freq_mhz(earfcn)
    if freq is None:
        return None
    # FSPL at 1m: 20*log10(f_MHz) + 32.44
    fspl_1m = 20.0 * math.log10(freq) + 32.44
    ref_loss = fspl_1m - gt_dbi - gr_dbi + system_losses_db
    return ref_loss

def estimate_bearing(cell_id):
    """
    تخمین جهت بر اساس رقم آخر Cell ID
    
    1 -> 45 درجه (NE)
    2 -> 135 درجه (SE)
    3 -> 225 درجه (SW)
    0 -> 315 درجه (NW)
    دیگر -> 0 درجه (N)
    """
    if not cell_id:
        return 0.0
    try:
        # Correct heuristic: extract the Sector ID (lowest 8 bits) then use its last digit
        sector = int(cell_id) % 256
        last_digit = int(str(sector % 10)[-1])
    except Exception:
        return 0.0
    
    bearing_map = {
        0: 315.0,  # NW
        1: 45.0,   # NE
        2: 135.0,  # SE
        3: 225.0,  # SW
        4: 0.0,    # N
        5: 90.0,   # E
        6: 180.0,  # S
        7: 270.0,  # W
        8: 45.0,   # NE
        9: 135.0,  # SE
    }
    
    return bearing_map.get(last_digit, 0.0)

def calculate_new_coordinates(lat, lon, distance_meters, bearing):
    """
    Compute destination point given start lat/lon, distance (meters) and bearing (degrees).
    Uses great-circle formula for higher accuracy.
    """
    R = 6371000.0
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brng = math.radians(bearing)
    d_div_r = distance_meters / R

    sin_lat2 = math.sin(lat1) * math.cos(d_div_r) + math.cos(lat1) * math.sin(d_div_r) * math.cos(brng)
    lat2 = math.asin(max(-1.0, min(1.0, sin_lat2)))

    y = math.sin(brng) * math.sin(d_div_r) * math.cos(lat1)
    x = math.cos(d_div_r) - math.sin(lat1) * math.sin(lat2)
    lon2 = lon1 + math.atan2(y, x)

    return {
        "lat": math.degrees(lat2),
        "lon": math.degrees(lon2)
    }


def weighted_centroid(towers):
    """Compute weighted centroid from list of towers.
    towers: iterable of dicts/items with 'lat','lon' and 'rsrp' (dBm) or 'weight'.
    Weighting: inverse of absolute RSRP (stronger -> larger weight).
    """
    sum_lat = 0.0
    sum_lon = 0.0
    sum_w = 0.0
    for t in towers:
        lat = t.get('lat')
        lon = t.get('lon')
        if lat is None or lon is None:
            continue
        if 'weight' in t:
            w = float(t['weight'])
        else:
            rsrp = t.get('rsrp')
            # avoid division by zero
            w = 1.0 / (abs(rsrp) + 1e-6) if rsrp is not None else 1.0
        sum_lat += lat * w
        sum_lon += lon * w
        sum_w += w
    if sum_w == 0:
        return None
    return {'lat': sum_lat / sum_w, 'lon': sum_lon / sum_w}


def trilaterate_three(t1, t2, t3):
    """Simple trilateration using three towers with lat, lon and radius (meters).
    Returns (lat, lon) or None on failure.
    Note: Converts lat/lon to Cartesian on an equirectangular approximation which is
    acceptable for small areas (few km). For larger areas use a proper geodetic solver.
    """
    # convert degrees to meters using local projection approx
    # pick reference
    lat0 = math.radians(t1['lat'])
    lon0 = math.radians(t1['lon'])
    R = 6371000.0

    def proj(t):
        # convert point degrees to radians then compute local planar coordinates
        lon_rad = math.radians(t['lon'])
        lat_rad = math.radians(t['lat'])
        x = R * (lon_rad - lon0) * math.cos(lat0)
        y = R * (lat_rad - lat0)
        return x, y

    x1, y1 = proj(t1)
    x2, y2 = proj(t2)
    x3, y3 = proj(t3)
    r1, r2, r3 = t1['radius'], t2['radius'], t3['radius']

    A = 2*(x2 - x1)
    B = 2*(y2 - y1)
    C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
    D = 2*(x3 - x2)
    E = 2*(y3 - y2)
    F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2

    denom = (A*E - B*D)
    if abs(denom) < 1e-6:
        return None

    x = (C*E - B*F) / denom
    y = (A*F - C*D) / denom

    # convert back to lat/lon (from reference lat0/lon0)
    lat_res_rad = lat0 + (y / R)
    lon_res_rad = lon0 + (x / (R * math.cos(lat0)))
    lat_res = math.degrees(lat_res_rad)
    lon_res = math.degrees(lon_res_rad)
    return lat_res, lon_res