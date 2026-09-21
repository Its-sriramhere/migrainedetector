# Migraine Detector — Personalized Migraine Early-Warning System

A full-stack IoT early-warning platform that combines physiological monitoring,
a personal health assessment, machine learning, and explainable AI to estimate
elevated migraine risk before an episode.

> Research prototype. This system estimates risk and provides explanations; it is
> **not** a medically validated diagnostic device.

## Repository layout

| Folder          | Purpose                                               |
|-----------------|-------------------------------------------------------|
| `frontend/`     | React + TypeScript + Vite + Tailwind web application  |
| `backend/`      | FastAPI API, SQLAlchemy models, WebSocket, ML runtime |
| `ml/`           | Training/evaluation scripts (scikit-learn, XGBoost, SHAP) |
| `raspberry-pi/` | Edge data-acquisition Python application              |
| `docs/`         | Architecture and API documentation                    |
| `tests/`        | Backend smoke tests                                   |

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # optional: SMS + override settings
python -m app.db.seed         # optional: ensure seed (also runs at startup)
uvicorn app.main:app --reload --port 8000
```

Docs: http://localhost:8000/docs

The default database is a local SQLite file (`migraine.db`). Set
`DATABASE_URL` to `postgresql+psycopg://...` to use PostgreSQL.

> Backend tests also need `numpy`, `pandas` and `httpx2` (installed alongside the
> calibration pipeline): `pip install numpy pandas httpx2`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

The app is an installable PWA (service worker + manifest). On Android/Chrome use
**Add to Home screen**; on iOS Safari use **Share → Add to Home Screen**.

## Datasets & threshold calibration

The bundled migraine datasets in `ml/datasets/` drive the deviation cutoffs and
baselines the risk engine uses — for both simulation and live monitoring:

- `ml/build_calibration_dataset.py` merges the BP / SpO2 / temperature files
  with the synthetic heart-rate dataset into `calibration.csv` (heart rate uses
  the `hr_abnormal` proxy label).
- `ml/calibrate.py` derives `backend/app/ml/thresholds.json` (band edges,
  per-signal triggers + weights, baselines, demo presets).

Both are exposed through the web UI at **Insights → Datasets** (and the API):

```
GET  /api/datasets                  list files + current thresholds
POST /api/datasets/build            rebuild ml/datasets/calibration.csv
POST /api/datasets/calibrate        recalibrate → thresholds.json (hot-reloads engine)
GET  /api/datasets/thresholds       current effective thresholds
GET  /api/datasets/download/{name}  download a dataset CSV
```

## SMS alerts

Alerts fire when the estimated risk crosses the calibrated band edge. SMS is
**off by default (mock provider)** and hard-capped with `SMS_MAX_SENDS` (default
5). To enable real Twilio SMS, fill `.env`:

```
SMS_ENABLED=true
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
ALERT_SMS_TO=+919360516302
ALERT_SMS_LEVEL=high        # high | moderate | all
SMS_MAX_SENDS=5
```

Before enabling, buy/select a Twilio phone number and verify the destination as
a Caller ID (trial accounts must verify recipients). Delivery is audited in
`notification_logs` and visible on the **Alerts** page.

## Demo mode

Inside the app, register an account, then open **Demo & Simulation** to push the
NORMAL / MODERATE / HIGH-RISK presets or a live simulated stream through the same
prediction pipeline used by the Raspberry Pi. Real and simulated data share one
pipeline by design.

## Raspberry Pi

`raspberry-pi/main.py` runs the edge application. Without physical hardware, it
runs in *demo source* mode and pushes simulated measurements to the backend so
the dashboard can be exercised.