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
    elif ta_int == 0:
        return 1 * 78.0
    return ta_int * 78.0


def haversine_distance(lat1, lon1, lat2, lon2):
    """calculate the great-circle distance between two points"""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_bearing_between_coords(lat1, lon1, lat2, lon2):
    """calculate the bearing (Azimuth) from point 1 to point 2"""
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lon2 - lon1))
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

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
    """Estimate bearing (degrees) from cell ID using heuristic on last digit of Sector ID."""
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
        1: 225.0,   # NE
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


def find_circle_intersections(lat1, lon1, r1, lat2, lon2, r2):
    """  find intersection points of two circles on Earth's surface."""
    d = haversine_distance(lat1, lon1, lat2, lon2)
    
    # کنترل خطا: دایره‌ها نمی‌رسند یا یکی داخل دیگری است
    if d > r1 + r2 or d < abs(r1 - r2) or d == 0:
        return []

    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h = math.sqrt(max(0, r1**2 - a**2))
    
    # نقطه میانی P2
    x2 = lat1 + a * (lat2 - lat1) / d
    y2 = lon1 + a * (lon2 - lon1) / d
    
    # ضرایب تبدیل (تقریبی برای فواصل کوتاه)
    m_per_deg_lat = 111000
    m_per_deg_lon = 111000 * math.cos(math.radians(lat1))
    
    # نقطه اول
    lat_i1 = x2 + (h * (lon2 - lon1) / d) / (m_per_deg_lat / 111000)
    lon_i1 = y2 - (h * (lat2 - lat1) / d) / (m_per_deg_lon / 111000)
    
    # نقطه دوم
    lat_i2 = x2 - (h * (lon2 - lon1) / d) / (m_per_deg_lat / 111000)
    lon_i2 = y2 + (h * (lat2 - lat1) / d) / (m_per_deg_lon / 111000)
    
    return [
        {'lat': lat_i1, 'lon': lon_i1},
        {'lat': lat_i2, 'lon': lon_i2}
    ]
    
def trilaterate_two_towers(t1, t2):
    """
    الگوریتم اصلی: محاسبه مکان با دو دکل
    """
    # 1. محاسبه شعاع اگر موجود نیست
    # نکته: می‌توانید مقدار n را اینجا دستی تنظیم کنید (مثلاً n=4.5)
    r1 = t1.get('radius')
    if r1 is None: r1 = calculate_distance(t1.get('rsrp'), tx_power=t1.get('tx_power'))
        
    r2 = t2.get('radius')
    if r2 is None: r2 = calculate_distance(t2.get('rsrp'), tx_power=t2.get('tx_power'))

    # 2. پیدا کردن نقاط تقاطع
    candidates = find_circle_intersections(
        t1['lat'], t1['lon'], r1,
        t2['lat'], t2['lon'], r2
    )
    
    # اگر تقاطع نداشتند، از روش قدیمی استفاده کن
    if not candidates:
        return weighted_centroid([t1, t2])
        
    # 3. انتخاب بهترین نقطه با بررسی سکتورها
    best_point = None
    min_score = float('inf')
    
    for p in candidates:
        score = 0
        # بررسی دکل 1
        b1 = calculate_bearing_between_coords(t1['lat'], t1['lon'], p['lat'], p['lon'])
        sec1 = estimate_bearing(t1.get('cellId') or t1.get('cell_id'))
        diff1 = abs(b1 - sec1)
        if diff1 > 180: diff1 = 360 - diff1
        score += diff1
        
        # بررسی دکل 2
        b2 = calculate_bearing_between_coords(t2['lat'], t2['lon'], p['lat'], p['lon'])
        sec2 = estimate_bearing(t2.get('cellId') or t2.get('cell_id'))
        diff2 = abs(b2 - sec2)
        if diff2 > 180: diff2 = 360 - diff2
        score += diff2
        
        if score < min_score:
            min_score = score
            best_point = p
            
    return best_point
    
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


def tower_weight(tower: dict) -> float:
    """
    Compute a small, stable weight for localization from radio metrics.
    - Stronger RSRP (closer to 0) => larger weight
    - Better RSRQ (closer to 0) => larger weight
    Falls back to 1.0.
    """
    rsrp = tower.get("rsrp")
    rsrq = tower.get("rsrq")
    w = 1.0
    try:
        if rsrp is not None:
            w *= 1.0 / max(1.0, abs(float(rsrp)))
    except Exception:
        pass
    try:
        if rsrq is not None:
            w *= 1.0 / max(1.0, abs(float(rsrq)))
    except Exception:
        pass
    # keep within sensible bounds
    return max(1e-6, min(w, 1.0))


def trilaterate_nlls(towers, max_iter: int = 25, damping: float = 1e-3, tol: float = 1e-3):
    """
    Non-linear least squares trilateration (Gauss-Newton + damping) on local tangent plane.
    Minimizes: sum_i w_i * (||p - p_i|| - r_i)^2

    towers: list of dicts with 'lat','lon','radius' (meters), optional 'rsrp','rsrq' for weighting.
    Returns (lat, lon) or None.
    """
    if not towers or len(towers) < 3:
        return None

    # Reference projection point
    lat0 = math.radians(towers[0]["lat"])
    lon0 = math.radians(towers[0]["lon"])
    R = 6371000.0

    def proj(lat_deg, lon_deg):
        lon_rad = math.radians(lon_deg)
        lat_rad = math.radians(lat_deg)
        x = R * (lon_rad - lon0) * math.cos(lat0)
        y = R * (lat_rad - lat0)
        return x, y

    pts = []
    for t in towers:
        if t.get("radius") is None:
            return None
        x, y = proj(t["lat"], t["lon"])
        pts.append((x, y, float(t["radius"]), tower_weight(t)))

    # Initial guess: weighted centroid of anchor points
    sw = sum(w for *_rest, w in pts)
    if sw <= 0:
        return None
    x = sum(px * w for px, py, r, w in pts) / sw
    y = sum(py * w for px, py, r, w in pts) / sw

    lam = float(damping)

    for _ in range(max_iter):
        # Build weighted normal equations for 2 variables (x,y)
        a11 = a12 = a22 = 0.0
        b1 = b2 = 0.0
        cost = 0.0

        for xi, yi, ri, wi in pts:
            dx = x - xi
            dy = y - yi
            di = math.hypot(dx, dy)
            if di < 1e-6:
                continue
            fi = di - ri
            # Jacobian
            jx = dx / di
            jy = dy / di
            wfi = wi * fi

            cost += wi * fi * fi
            a11 += wi * jx * jx
            a12 += wi * jx * jy
            a22 += wi * jy * jy
            b1 += jx * wfi
            b2 += jy * wfi

        # Solve (A + lam I) * delta = -b
        a11_d = a11 + lam
        a22_d = a22 + lam
        det = a11_d * a22_d - a12 * a12
        if abs(det) < 1e-12:
            return None

        dx_step = (-b1 * a22_d - (-b2) * a12) / det
        dy_step = (a11_d * (-b2) - a12 * (-b1)) / det

        if math.hypot(dx_step, dy_step) < tol:
            break

        x_new = x + dx_step
        y_new = y + dy_step

        # Simple acceptance: if cost decreases, accept and reduce damping; else increase damping
        new_cost = 0.0
        for xi, yi, ri, wi in pts:
            di = math.hypot(x_new - xi, y_new - yi)
            fi = di - ri
            new_cost += wi * fi * fi

        if new_cost <= cost or cost == 0.0:
            x, y = x_new, y_new
            lam = max(1e-6, lam * 0.5)
        else:
            lam = min(1e6, lam * 2.0)

    # Convert back to lat/lon
    lat_res_rad = lat0 + (y / R)
    lon_res_rad = lon0 + (x / (R * math.cos(lat0)))
    return math.degrees(lat_res_rad), math.degrees(lon_res_rad)


def trilaterate_three(t1, t2, t3):
    """Simple trilateration using three towers with lat, lon and radius (meters).
    Returns (lat, lon) or None on failure.
    Note: Converts lat/lon to Cartesian on an equirectangular approximation which is
    acceptable for small areas (few km). For larger areas use a proper geodetic solver.
    """
    # Prefer NLLS when possible; fallback to linear solver below.
    nlls = trilaterate_nlls([t1, t2, t3])
    if nlls:
        return nlls

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
