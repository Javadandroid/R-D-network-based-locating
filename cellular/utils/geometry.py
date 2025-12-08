import math

def calculate_distance(rsrp, tx_power=45, n=5.2):
    """
    محاسبه فاصله با فرمول Path Loss
    
    فرمول: Path Loss = TX - RX = 10*n*log10(d) + C
    پس: d = 10^((TX - RX - C) / (10*n))
    
    برای تهران (Urban):
    - TX: 40 dBm (پیش‌فرض)
    - n: 3.5-4.0 (منطقه شهری)
    - C: ~70-85 (ثابت محیط)
    """
    if rsrp is None or rsrp == 0:
        return 500.0  # مقدار پیش‌فرض
    
    rsrp = -abs(rsrp)  # سیگنال همیشه منفی است
    
    try:
        # Path Loss = TX - RX
        path_loss = tx_power - rsrp
        
        # d = 10^((PL - 80) / (10*n))
        # 80 = Reference Loss at 1m
        distance = math.pow(10, (path_loss - 80) / (10 * n))
        
        # محدود کردن به [50, 5000] متر
        distance = max(50, min(distance, 5000))
        
        return distance
    except Exception as e:
        print(f"خطا در محاسبه فاصله: {e}")
        return 500.0

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
    last_digit = int(str(cell_id % 10)[-1])
    
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
    R = 6371000  # Earth radius in meters

    # Convert to radians
    lat_rad = math.radians(lat)
    bearing = math.radians(bearing)

    # Component distances
    dn = distance_meters * math.cos(bearing)  # north component
    de = distance_meters * math.sin(bearing)  # east component

    # Convert to degrees offset
    dlat = dn / R
    dlon = de / (R * math.cos(lat_rad))

    # New position
    new_lat = lat + math.degrees(dlat)
    new_lon = lon + math.degrees(dlon)
    
    return {
        "lat": new_lat,
        "lon": new_lon
    }