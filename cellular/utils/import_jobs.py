import threading
import uuid
from typing import Dict, Any, Optional

_jobs: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def create_job() -> str:
    job_id = uuid.uuid4().hex
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "PENDING",
            "total_rows": 0,
            "processed_rows": 0,
            "errors": [],
            "last_updates": [],
        }
    return job_id


def update_job(job_id: str, **fields: Any) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job.update(fields)


def append_update(job_id: str, update: Dict[str, Any], max_items: int = 10) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        updates = job.get("last_updates") or []
        updates.append(update)
        job["last_updates"] = updates[-max_items:]


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return None
        return dict(job)
