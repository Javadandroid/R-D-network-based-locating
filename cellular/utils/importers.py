import csv
import io
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from cellular.models import CellTower
from cellular.choices import DatasetSource
from .import_jobs import update_job, append_update

# field mapping for csv
CSV_FIELD_MAPPING: Dict[str, Sequence[str]] = {
    "radio_type": ("radio_type", "radioType", "radio", "rat"),
    "mcc": ("mcc", "MCC"),
    "mnc": ("mnc", "MNC"),
    "lac": ("lac", "LAC", "tac", "TAC"),
    "cell_id": ("cell_id", "cellId", "cid", "eci", "CellID"),
    "pci": ("pci", "PCI", "physicalCellId"),
    "earfcn": ("earfcn", "EARFCN", "frequency", "freq"),
    "range_m": ("range_m", "range", "coverage", "rangeMeters"),
    "lat": ("lat", "latitude", "Latitude"),
    "is_approximate": ("is_approximate", "approximate", "isApproximate", "changeable"),
    "samples": ("samples", "num_samples", "measurements"),
    "lon": ("lon", "lng", "longitude", "Longitude"),
    "tx_power": ("tx_power", "txPower", "TxPower", "txp"),
    "antenna_azimuth": ("antenna_azimuth", "azimuth", "bearing"),
    "source": ("source", "data_source"),
}

BATCH_SIZE = 1000
LOOKUP_BATCH_SIZE = 200


PROGRESS_UPDATE_SIZE = 200


def import_towers_from_csv(
    file_obj,
    dataset_source: str = DatasetSource.OTHER,
    update_existing: bool = True,
    job_id: Optional[str] = None,
) -> Dict[str, int]:

    created_instances: List[CellTower] = []
    rows_to_update: List[CellTower] = []
    errors: List[str] = []
    existing_lookup: Dict[Tuple[int, int, int, Optional[int]], CellTower] = {}
    seen_new_keys: set = set()

    text_wrapper = _ensure_text_mode(file_obj)
    reader = csv.DictReader(text_wrapper)

    normalized_rows = []
    for idx, raw_row in enumerate(reader, start=2):  # 1 برای header
        try:
            normalized = _normalize_row(raw_row, default_source=dataset_source)
            normalized_rows.append(normalized)
        except ValueError as exc:
            errors.append(f"خط {idx}: {exc}")

    if not normalized_rows:
        return {"created": 0, "updated": 0, "errors": errors}

    existing_lookup = _fetch_existing_lookup(normalized_rows)

    processed_rows = 0
    total_rows = len(normalized_rows)
    if job_id:
        update_job(
            job_id,
            status="IN_PROGRESS",
            total_rows=total_rows,
            processed_rows=0,
            errors=errors,
        )

    for row in normalized_rows:
        processed_rows += 1
        key = (row["mcc"], row["mnc"], row["cell_id"], row["lac"])
        instance = existing_lookup.get(key)
        new_samples = row.get("samples") or 0
        action = "created"
        old_samples = None
        old_lat = None
        old_lon = None

        if instance:
            action = "skipped"
            old_samples = instance.samples or 0
            old_lat, old_lon = instance.lat, instance.lon

            if new_samples > old_samples:
                action = "updated_samples"
                if update_existing:
                    _apply_row_to_instance(instance, row)
                    instance.samples = new_samples
                    rows_to_update.append(instance)
                instance.checked_count = (instance.checked_count or 0) + 1
            elif new_samples == old_samples:
                action = "verified"
                instance.checked_count = (instance.checked_count or 0) + 1
                instance.verified_count = (instance.verified_count or 0) + 1
                if update_existing:
                    rows_to_update.append(instance)
            else:
                instance.checked_count = (instance.checked_count or 0) + 1
                if update_existing:
                    rows_to_update.append(instance)
        else:
            if key in seen_new_keys:
                continue  # تکراری در همان فایل
            seen_new_keys.add(key)
            new_tower = CellTower(**row)
            new_tower.checked_count = 1
            new_tower.verified_count = 1
            created_instances.append(new_tower)
            old_lat, old_lon = None, None
            old_samples = None
            action = "created"

        if job_id and processed_rows % PROGRESS_UPDATE_SIZE == 0:
            update_job(job_id, processed_rows=processed_rows)
            append_update(
                job_id,
                {
                    "key": {
                        "mcc": key[0],
                        "mnc": key[1],
                        "cell_id": key[2],
                        "lac": key[3],
                    },
                    "action": action,
                    "old_samples": old_samples,
                    "new_samples": new_samples,
                    "old_lat": old_lat,
                    "old_lon": old_lon,
                    "new_lat": row.get("lat"),
                    "new_lon": row.get("lon"),
                },
            )

    if job_id:
        update_job(job_id, processed_rows=processed_rows)

    created_count = 0
    updated_count = 0

    with transaction.atomic():
        for chunk in _chunked(created_instances, BATCH_SIZE):
            CellTower.objects.bulk_create(chunk, ignore_conflicts=True)
            created_count += len(chunk)

        if update_existing and rows_to_update:
            # bulk_update does not trigger auto_now, so update timestamps manually.
            now = timezone.now()
            deduped: Dict[int, CellTower] = {}
            for obj in rows_to_update:
                if obj.pk is not None:
                    obj.updated_at = now
                    deduped[int(obj.pk)] = obj
            rows_to_update = list(deduped.values())

            CellTower.objects.bulk_update(
                rows_to_update,
                [
                    "radio_type",
                    "mcc",
                    "mnc",
                    "lac",
                    "cell_id",
                    "pci",
                    "earfcn",
                    "range_m",
                    "is_approximate",
                    "samples",
                    "lat",
                    "lon",
                    "tx_power",
                    "antenna_azimuth",
                    "source",
                    "checked_count",
                    "verified_count",
                    "updated_at",
                ],
                batch_size=BATCH_SIZE,
            )
            updated_count = len(rows_to_update)

    result = {"created": created_count, "updated": updated_count, "errors": errors}
    if job_id:
        update_job(job_id, processed_rows=total_rows, status="SUCCESS", result=result)
    return result


def _ensure_text_mode(file_obj):
    if isinstance(file_obj, io.TextIOBase):
        file_obj.seek(0)
        return file_obj
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)
    return io.TextIOWrapper(file_obj, encoding="utf-8")


def _fetch_existing_lookup(
    rows: List[Dict],
) -> Dict[Tuple[int, int, int, Optional[int]], CellTower]:
    if not rows:
        return {}

    keys = []
    for row in rows:
        keys.append((row["mcc"], row["mnc"], row["cell_id"], row["lac"]))

    lookup: Dict[Tuple[int, int, int, Optional[int]], CellTower] = {}

    for chunk in _chunked(keys, LOOKUP_BATCH_SIZE):
        conditions = []
        for mcc, mnc, cell_id, lac in chunk:
            condition = Q(mcc=mcc, mnc=mnc, cell_id=cell_id)
            if lac is None:
                condition &= Q(lac__isnull=True)
            else:
                condition &= Q(lac=lac)
            conditions.append(condition)

        if not conditions:
            continue

        combined_condition = conditions[0]
        for condition in conditions[1:]:
            combined_condition |= condition

        queryset = CellTower.objects.filter(combined_condition)
        for tower in queryset:
            key = (tower.mcc, tower.mnc, tower.cell_id, tower.lac)
            lookup[key] = tower
    return lookup


def _normalize_row(raw_row: Dict[str, str], default_source: str) -> Dict:
    def read_value(field_name: str):
        for column in CSV_FIELD_MAPPING.get(field_name, []):
            if column in raw_row:
                value = raw_row[column]
                if value not in ("", None):
                    return value
        return None

    try:
        mcc = _to_int(read_value("mcc"), required=True)
        mnc = _to_int(read_value("mnc"), required=True)
        cell_id = _to_int(read_value("cell_id"), required=True)
    except ValueError as exc:
        raise ValueError(f"required fields are missing: {exc}")

    lac = _to_int(read_value("lac"))
    radio_type_value = read_value("radio_type")
    radio_type = (
        radio_type_value.lower() if radio_type_value else None
    ) or CellTower._meta.get_field("radio_type").default
    pci = _to_int(read_value("pci"))
    earfcn = _to_int(read_value("earfcn"))
    range_m = _to_int(read_value("range_m"))
    is_approximate = _to_int(read_value("is_approximate")) == 1
    samples = _to_int(read_value("samples"))
    lat = _to_float(read_value("lat"), required=True)
    lon = _to_float(read_value("lon"), required=True)
    tx_power = (
        _to_int(read_value("tx_power")) or CellTower._meta.get_field("tx_power").default
    )
    antenna_azimuth = _to_int(read_value("antenna_azimuth"))
    row_source = read_value("source") or default_source

    return {
        "radio_type": radio_type,
        "mcc": mcc,
        "mnc": mnc,
        "lac": lac,
        "cell_id": cell_id,
        "pci": pci,
        "earfcn": earfcn,
        "range_m": range_m,
        "is_approximate": is_approximate,
        "samples": samples,
        "lat": lat,
        "lon": lon,
        "tx_power": tx_power,
        "antenna_azimuth": antenna_azimuth,
        "source": row_source,
    }


def _apply_row_to_instance(instance: CellTower, row: Dict) -> None:
    for field, value in row.items():
        setattr(instance, field, value)


def _to_int(value, required: bool = False) -> Optional[int]:
    if value in (None, ""):
        if required:
            raise ValueError("Value is required but missing")
        return None
    try:
        if isinstance(value, str):
            value = value.strip()
        return int(float(value))
    except (TypeError, ValueError):
        if required:
            raise ValueError(f"Value '{value}' is not a number")
        return None


def _to_float(value, required: bool = False) -> Optional[float]:
    if value in (None, ""):
        if required:
            raise ValueError("Coordinate is required but missing")
        return None
    try:
        if isinstance(value, str):
            value = value.strip()
        return float(value)
    except (TypeError, ValueError):
        if required:
            raise ValueError(f"Value '{value}' is not a number")
        return None


def _chunked(items: Sequence[CellTower], size: int) -> Iterable[Sequence[CellTower]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]
