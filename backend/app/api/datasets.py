"""Dataset management API.

Lets authenticated users list the bundled migraine datasets, rebuild the merged
calibration CSV, re-run calibration into ``thresholds.json`` and download any of
the files. The live engine + baseline fallbacks hot-reload after calibration so
simulation and live monitoring immediately use the new thresholds.
"""
import csv
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..core.config import settings
from ..core.security import utcnow
from ..db.session import get_db
from ..models import DatasetFile, User

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

ML_DIR = Path(settings.DATASET_DIR)
BUILD_SCRIPT = Path(settings.DATASET_DIR).resolve().parents[1] / "ml" / "build_calibration_dataset.py"
CALIBRATE_SCRIPT = Path(settings.DATASET_DIR).resolve().parents[1] / "ml" / "calibrate.py"

DEFAULT_LABEL_COLS = {"heart_rate": "hr_abnormal"}


class CalibrateIn(BaseModel):
    file: str = "calibration.csv"
    label_col: str = "episode"
    label_cols: dict[str, str] = DEFAULT_LABEL_COLS
    band_low: Optional[float] = None
    band_high: Optional[float] = None


def _csv_info(path: Path) -> dict:
    size = path.stat().st_size
    rows = 0
    columns: list[str] = []
    try:
        with open(path, encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header:
                columns = header
            for _ in reader:
                rows += 1
    except Exception:  # noqa: BLE001
        rows = -1
    return {
        "name": path.name,
        "size_bytes": size,
        "rows": rows,
        "columns": columns,
        "modified": path.stat().st_mtime,
    }


def _storage_base() -> str:
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        raise HTTPException(
            501,
            "Supabase is not configured. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in backend/.env",
        )
    return settings.SUPABASE_URL.rstrip("/")


def _storage_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
    }


def _ensure_storage_bucket(base: str, bucket: str, headers: dict) -> None:
    try:
        req = urllib.request.Request(f"{base}/storage/v1/bucket/{bucket}", headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status in (200, 201):
                return
    except urllib.error.HTTPError as exc:
        if exc.code not in (400, 404):
            raise HTTPException(502, f"could not inspect storage bucket: HTTP {exc.code}")

    body = json.dumps({"id": bucket, "name": bucket, "public": False}).encode()
    try:
        req = urllib.request.Request(
            f"{base}/storage/v1/bucket",
            data=body,
            headers={**headers, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(f"create bucket returned HTTP {resp.status}")
    except urllib.error.HTTPError as exc:
        raise HTTPException(502, f"could not create bucket '{bucket}': HTTP {exc.code}")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"could not create bucket '{bucket}': {exc}")


def _upload_dataset_object(base: str, key: str, content: bytes, headers: dict) -> None:
    try:
        req = urllib.request.Request(
            f"{base}/storage/v1/object/{key}",
            data=content,
            headers={**headers, "Content-Type": "text/csv; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(f"upload returned HTTP {resp.status}")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"upload returned HTTP {exc.code}: {exc.read()[:200]!r}")


@router.get("")
def list_datasets(current: User = Depends(get_current_user)):
    from ..services.prediction_service import ENGINE

    files = []
    if ML_DIR.is_dir():
        for path in sorted(ML_DIR.glob("*.csv")):
            files.append(_csv_info(path))

    stored_rows = {}
    try:
        with SessionLocal() as stored_db:
            for row in stored_db.execute(select(DatasetFile)).scalars():
                stored_rows[row.name] = row
    except Exception:  # noqa: BLE001
        pass

    for f in files:
        row = stored_rows.get(f["name"])
        f["stored"] = bool(row and row.stored)
        f["storage_bucket"] = row.storage_bucket if row else settings.SUPABASE_STORAGE_BUCKET
        f["storage_key"] = row.storage_key if row else ""

    thresholds = ENGINE.config_snapshot()

    from ..db.session import SessionLocal
    from ..services.notifications import _real_sends_used

    sms_used = 0
    try:
        with SessionLocal() as sms_db:
            sms_used = _real_sends_used(sms_db)
    except Exception:  # noqa: BLE001
        pass

    db_url = str(settings.DATABASE_URL)
    if db_url.startswith("sqlite"):
        db_file = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not Path(db_file).is_absolute():
            db_file = str(Path(db_file).resolve())
        db_label = "SQLite database file"
    else:
        db_file = db_url
        db_label = "Relational database"

    storage = {
        "database": {
            "url": db_file,
            "label": db_label,
            "note": "app data: users, sensor_readings, predictions, alerts, notification_logs",
        },
        "datasets_dir": str(ML_DIR),
        "thresholds_path": ENGINE.config_path,
        "export_note": "Readings/predictions export from the Reports page",
        "sms": {
            "provider": settings.SMS_PROVIDER,
            "enabled": settings.SMS_ENABLED,
            "recipient": settings.ALERT_SMS_TO or "unset",
            "level": settings.ALERT_SMS_LEVEL,
            "max_sends": settings.SMS_MAX_SENDS,
            "sends_used": sms_used,
        },
        "supabase": {
            "enabled": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY),
            "url": settings.SUPABASE_URL or "",
            "project_ref": settings.SUPABASE_PROJECT_REF or "",
            "bucket": settings.SUPABASE_STORAGE_BUCKET,
            "stored_count": sum(1 for f in files if f.get("stored")),
        },
    }
    return {
        "datasets_dir": str(ML_DIR),
        "files": files,
        "thresholds": thresholds,
        "storage": storage,
    }


@router.post("/build")
def build_calibration_dataset(current: User = Depends(get_current_user)):
    if not BUILD_SCRIPT.is_file():
        raise HTTPException(404, f"build script not found: {BUILD_SCRIPT}")
    if not ML_DIR.is_dir():
        raise HTTPException(404, f"datasets dir not found: {ML_DIR}")
    try:
        result = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT), "--input", str(ML_DIR)],
            capture_output=True, text=True, timeout=900,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(408, "build timed out")
    if result.returncode != 0:
        raise HTTPException(500, f"build failed:\n{result.stderr[-2000:]}")
    out = ML_DIR / "calibration.csv"
    info = _csv_info(out) if out.is_file() else {}
    return {"ok": True, "output": str(out), "file": info, "log_tail": result.stdout[-2000:]}


@router.post("/calibrate")
def run_calibration(body: CalibrateIn, current: User = Depends(get_current_user)):
    if not CALIBRATE_SCRIPT.is_file():
        raise HTTPException(404, f"calibrate script not found: {CALIBRATE_SCRIPT}")

    src = ML_DIR / body.file
    if not src.is_file():
        raise HTTPException(404, f"data file not found: {src}")

    out_path = Path(settings.THRESHOLDS_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, str(CALIBRATE_SCRIPT),
        "--data", str(src),
        "--label-col", body.label_col,
        "--label-cols", json.dumps(body.label_cols),
        "--output", str(out_path),
    ]
    if body.band_low is not None:
        cmd += ["--band-low", str(body.band_low)]
    if body.band_high is not None:
        cmd += ["--band-high", str(body.band_high)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        raise HTTPException(408, "calibration timed out")
    if result.returncode != 0:
        raise HTTPException(500, f"calibration failed:\n{result.stderr[-2000:]}")

    # Hot-reload the live engine + baseline fallbacks with the new thresholds.
    from ..services.prediction_service import reload_engine

    reload_engine()

    config = {}
    try:
        with open(out_path, encoding="utf-8") as fh:
            config = json.load(fh)
    except Exception:  # noqa: BLE001
        pass

    return {
        "ok": True,
        "output": str(out_path),
        "config": config,
        "log_tail": result.stdout[-2000:],
    }


@router.get("/thresholds")
def get_thresholds(current: User = Depends(get_current_user)):
    from ..services.prediction_service import ENGINE

    return {
        "path": ENGINE.config_path,
        "calibrated": ENGINE.calibrated,
        "baselines": ENGINE.baselines,
        "band_edges": {"low": ENGINE.band_low, "high": ENGINE.band_high},
        "deviations": ENGINE.config_snapshot().get("deviations", {}),
        "demo_presets": ENGINE.demo_presets,
    }


@router.get("/download/{filename}")
def download_dataset(filename: str, current: User = Depends(get_current_user)):
    safe = Path(filename).name
    path = (ML_DIR / safe)
    if not path.is_file():
        raise HTTPException(404, "file not found")
    content = path.read_bytes()
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={safe}"},
    )


@router.post("/supabase-sync")
def supabase_sync(db: Session = Depends(get_db),
                  current: User = Depends(get_current_user)):
    """Upload every bundled CSV to a Supabase Storage bucket and record metadata.

    Uses the service-role key (server-side only), never a client key.
    """
    if not ML_DIR.is_dir():
        raise HTTPException(404, f"datasets dir not found: {ML_DIR}")

    base = _storage_base()
    bucket = settings.SUPABASE_STORAGE_BUCKET
    headers = _storage_headers()
    _ensure_storage_bucket(base, bucket, headers)

    results = []
    stored = 0
    for path in sorted(ML_DIR.glob("*.csv")):
        name = path.name
        info = _csv_info(path)
        key = f"{bucket}/{name}"
        try:
            _upload_dataset_object(base, key, path.read_bytes(), headers)
        except Exception as exc:  # noqa: BLE001
            results.append({"name": name, "ok": False, "error": str(exc)[:200]})
            continue

        row = db.execute(
            select(DatasetFile).where(DatasetFile.name == name)
        ).scalar_one_or_none()
        if row is None:
            row = DatasetFile(name=name)
            db.add(row)
        row.path = str(path)
        row.rows = info["rows"]
        row.columns = info["columns"]
        row.size_bytes = info["size_bytes"]
        row.modified = info["modified"]
        row.storage_bucket = bucket
        row.storage_key = key
        row.stored = True
        row.uploaded_at = utcnow()
        results.append({"name": name, "ok": True, "storage_key": key})
        stored += 1

    db.commit()
    return {
        "ok": True,
        "project_url": settings.SUPABASE_URL,
        "bucket": bucket,
        "stored": stored,
        "failed": len(results) - stored,
        "files": results,
    }