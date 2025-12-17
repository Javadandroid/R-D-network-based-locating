"""
Data cleaning helpers for incoming cell reports.
Implements sentinel filtering described in R&DDocs.md
"""

SENTINEL_INT_MAX = 2147483647
SENTINEL_TAC = 65535
SENTINEL_CI = 268435455


def is_valid_cell(cell):
    """Return True if the provided cell dict passes basic validity checks."""
    try:
        mcc = cell.get("mcc")
        mnc = cell.get("mnc")
        cid = cell.get("cellId")
        lac = cell.get("lac")
        rsrp = cell.get("signalStrength")
    except Exception:
        return False

    if mcc in (None, SENTINEL_INT_MAX) or mnc in (None, SENTINEL_INT_MAX):
        return False

    if cid in (None, SENTINEL_INT_MAX, SENTINEL_CI):
        return False

    if lac in (SENTINEL_TAC,):
        return False

    # signal strength should be a negative dBm value in most cases
    if rsrp is None:
        return False
    try:
        if not (-140 <= int(rsrp) <= -20):
            # still accept but mark invalid if out of realistic range
            return False
    except Exception:
        return False

    return True


def clean_cells(cells):
    """Filter a list of incoming cell dicts and return only valid ones.
    Preserves ordering but removes entries failing sentinel checks.
    """
    if not cells:
        return []
    cleaned = []
    for c in cells:
        if is_valid_cell(c):
            cleaned.append(c)
    return cleaned
