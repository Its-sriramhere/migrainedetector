# Architecture

Migraine Detector is a full-stack, research-grade early-warning prototype. A Raspberry Pi
reads physiological signals, a FastAPI backend computes personalized risk, and a React
frontend presents live status, predictions and explanations.

```
┌──────────────────┐   MQTT/HTTPS    ┌──────────────────┐
│  Raspberry Pi    │ ───────────────▶│  FastAPI backend │
│  sensors + edge  │   /api/sensor   │  SQLAlchemy/SQLite│
│  buffering       │                 │  heuristic engine │
└──────────────────┘                 └────────┬─────────┘
                                              │  WebSocket
                ┌─────────────────────────────┼─────────┐
                ▼                             ▼          ▼
        ┌──────────────┐          ┌──────────────┐  ┌──────────────┐
        │  React/Vite  │          │  demo lab    │  │  ML scripts  │
        │  dashboard   │          │  (simulated) │  │  training    │
        └──────────────┘          └──────────────┘  └──────────────┘
```

## Layers

- **Frontend** (`frontend/`) — React 18 + TypeScript + Vite. Tailwind-driven design
  tokens in `src/styles/theme.css`; custom CSS in `src/styles/`. Recharts for time series.
  WebSocket client with auto-reconnect in `src/services/websocket.ts`; realtime state
  centralized in `src/context/LiveContext.tsx`.
- **Backend** (`backend/`) — FastAPI. SQLite by default; set `DATABASE_URL` for
  PostgreSQL. JWT + bcrypt auth. In-process heuristic engine powers predictions until a
  trained model is available.
- **Edge** (`raspberry-pi/`) — package that reads MAX30102 (HR/SpO₂), a blood-pressure
  module, MPU6050 (activity) and MAX30205 (temperature), validates signal quality,
  buffers locally (SQLite) and uploads to the backend.
- **ML** (`ml/`) — scripts to run once real labeled data exists: preprocessing,
  feature engineering, train (Logistic Regression / Random Forest / XGBoost),
  leakage-safe evaluate, predict and SHAP explain. `ml/ingest_dataset.py` converts
  exported readings+episodes into training format; `ml/calibrate.py` derives the
  heuristic engine's `thresholds.json` from a labeled CSV
  (schema in `ml/dataset.schema.example.csv`).

## Notifications & dataset export

- **SMS/notification service** (`app/services/notifications.py`): a
  `NotificationProvider` interface with `MockSmsProvider` (console + DB log) and
  `TwilioSmsProvider` (enabled via `SMS_ENABLED`/`SMS_PROVIDER=twilio`). Every alert
  attempt is written to the `notification_logs` table for audit.
- **Dataset export** (`app/api/dataset.py`): all readings + the risk at each
  reading's time as CSV/JSON, capped by `EXPORT_MAX_ROWS`. This is the raw feed for
  future real-data training and threshold calibration.
- **Device heartbeat** (`POST /api/devices/heartbeat`): the Pi pings every
  `HEARTBEAT_INTERVAL` (60s) so the dashboard reflects live online/offline status.
- **Reports** (`app/api/reports.py`): `predictions.csv` and `episodes.csv` for
  downloads; the frontend prints the reports page to PDF via `window.print()`.

## Core flow

1. User answers 14 seeded questions (`/api/assessment/questions`).
2. Backend builds a personal profile and baseline (`db/seed.py`, `services/baseline_service.py`).
3. Sensor readings arrive (`/api/sensor/readings`) or a demo preset is pushed
   (`/api/demo/scenario`) — both go through `services/prediction_service.create_prediction`.
4. `HeuristicEngine` (or the loaded model) estimates risk; features are attributed
   (SHAP-style) and stored.
5. Alerts are created above risk thresholds; `prediction_update` / `alert_update` are
   broadcast over `/ws/{user_id}`.
6. The frontend renders risk, live sensors, feature importance, alerts and reports.

## Risk bands

- `<30` low, `30–70` moderate, `>70` high.

## Demo mode

`/api/demo/start` runs an asyncio stream interpolating NORMAL → MODERATE-HIGH signal
presets through the exact prediction pipeline. `app.state.demo` holds per-user tasks;
`settings.DEMO_INTERVAL_SECONDS` (2.5s) controls cadence.

## Security

- Passwords hashed with bcrypt; JWT for stateless auth.
- WebSocket requires `?token=` and matches `user_id`.
- CORS locked to the Vite dev origins.
- `.env.example` documents all config; never commit real secrets.

## Running

```bash
# backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev   # http://localhost:5173  (proxies /api and /ws to :8000)

# backend tests
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
```