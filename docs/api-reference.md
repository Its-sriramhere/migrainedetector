# API Reference

Base URL: `http://localhost:8000`. Interactive docs at `/docs`.

Authentication: `Authorization: Bearer <access_token>` on protected routes.

## Auth

| Method | Path                | Body                                            | Returns          |
| ------ | ------------------- | ----------------------------------------------- | ---------------- |
| POST   | `/api/auth/register`| `{name, email, password, consent_given}`        | `{access_token, token_type}` |
| POST   | `/api/auth/login`   | `{email, password}`                             | `{access_token, token_type}` |

## Users

| Method | Path           | Description                     |
| ------ | -------------- | ------------------------------- |
| GET    | `/api/users/me`| Current user profile            |

## Assessment

| Method | Path                           | Description                                  |
| ------ | ------------------------------ | -------------------------------------------- |
| GET    | `/api/assessment/questions`    | 14 active seeded questions                    |
| POST   | `/api/assessment/responses`    | `{answers: [{question_id, answer}]}` → builds profile |
| GET    | `/api/assessment/profile`      | Current `UserRiskProfile`                     |
| GET    | `/api/assessment/baseline`     | Learned baseline (heart-rate band, sleep…)    |

## Devices

| Method | Path                    | Description                          |
| ------ | ----------------------- | ------------------------------------ |
| POST   | `/api/devices/register` | Register/claim a Pi `{device_identifier, device_name}` |
| POST   | `/api/devices/heartbeat`| Pi liveness ping `{device_identifier, device_name}` → `{status, last_seen}` (404 if unregistered) |
| GET    | `/api/devices`          | List user devices                     |
| GET    | `/api/devices/{id}/status` | Device status incl. `last_seen`    |

## Sensor data

| Method | Path                    | Description                                        |
| ------ | ----------------------- | -------------------------------------------------- |
| GET    | `/api/sensor/latest`    | Latest `SensorReading`                             |
| GET    | `/api/sensor/history?limit=N` | Recent readings (newest first)              |
| POST   | `/api/sensor/readings`  | Ingest a reading; returns `{reading, prediction}`  |

Sensor fields: `heart_rate`, `hrv`, `systolic_bp`, `diastolic_bp`, `spo2`,
`temperature`, `activity`, `signal_quality`, `source`, `timestamp`.

## Predictions

| Method | Path                             | Description                          |
| ------ | -------------------------------- | ------------------------------------ |
| GET    | `/api/predictions/current`       | Most recent prediction                |
| GET    | `/api/predictions/history?limit=N` | Recent predictions with `features` |
| POST   | `/api/predictions/predict`       | One-off `PredictRequest` → risk + explanation |
| POST   | `/api/predictions/{id}/outcome`  | Record episode outcome                |

## Migraine episodes

| Method | Path                   | Description                          |
| ------ | ---------------------- | ------------------------------------ |
| POST   | `/api/migraine`        | Create episode `{start_time, end_time?, severity?, symptoms[], trigger?, notes?}` |
| GET    | `/api/migraine/history`| List episodes (newest first)          |
| PUT    | `/api/migraine/{id}`   | Update episode                        |

## Alerts

| Method | Path                                 | Description                          |
| ------ | ------------------------------------ | ------------------------------------ |
| GET    | `/api/alerts?limit=N`                | List alerts                           |
| POST   | `/api/alerts/{id}/acknowledge`       | Mark acknowledged                     |
| POST   | `/api/alerts/{id}/feedback`          | `{feedback: "yes"\|"no"\|"not_sure"}` |

## Demo

| Method | Path                 | Description                                    |
| ------ | -------------------- | ---------------------------------------------- |
| GET    | `/api/demo/status`   | `{running, scenario}`                          |
| POST   | `/api/demo/scenario` | Push one preset `{scenario: normal\|moderate\|high}` → `{reading, prediction}` |
| POST   | `/api/demo/sensor-data` | Push arbitrary sensor payload as demo source |
| POST   | `/api/demo/start`    | Start streaming scenario (asyncio)              |
| POST   | `/api/demo/stop`     | Stop the running stream                         |

## Reports

| Method | Path               | Description                                        |
| ------ | ------------------ | -------------------------------------------------- |
| GET    | `/api/reports/overview` | Totals, latest/avg risk, `risk_band_counts`, `days_monitored` |
| GET    | `/api/reports/predictions.csv` | All predictions as CSV (auth'd download)    |
| GET    | `/api/reports/episodes.csv`    | All episodes as CSV (auth'd download)       |

## Dataset export

| Method | Path                    | Description                                          |
| ------ | ----------------------- | ---------------------------------------------------- |
| GET    | `/api/dataset/export.csv`  | All stored readings + the risk score/level current at each reading's time (capped by `EXPORT_MAX_ROWS`, default 10000) |
| GET    | `/api/dataset/export.json` | Same data as JSON                                      |

The dataset feed powers `ml/ingest_dataset.py` (→ training format) and
`ml/calibrate.py` (→ `backend/app/ml/thresholds.json`). See `ml/dataset.schema.example.csv`.

## SMS alerts

Alerts are published over WebSocket and (optionally) sent as SMS. Configuration
(`backend/.env`, see `.env.example`): `SMS_ENABLED`, `SMS_PROVIDER=mock|twilio`,
`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `ALERT_SMS_TO`,
`ALERT_SMS_LEVEL`. Every attempt is recorded in the `notification_logs` table
(`kind=sms`, `status=sent|skipped|failed`, `risk_level`, `message`).

## Prediction model

`Prediction` fields: `risk_score (0–100)`, `risk_level (low|moderate|high)`,
`prediction_window` (minutes), `model_version`, `source`, `features` (list of
`{feature_name, feature_value, contribution}`).

## WebSocket

`ws://localhost:8000/ws/{user_id}?token=<access_token>`

Events (JSON):

- `prediction_update` — new risk estimate `{type, risk_score, risk_level, timestamp, prediction_window_minutes, features}`
- `alert_update` — new alert `{type, id, risk_score, risk_level, message, timestamp, acknowledged, prediction_id}`

The client reconnects with exponential backoff (`services/websocket.ts`).