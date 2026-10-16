# RiskLens AI — Explainable Payment Fraud Risk Management System

> **Razorpay AI Buildathon — AI Risk Manager Track**

[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143.1-009688)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB)](https://react.dev)
[![Tests](https://img.shields.io/badge/tests-77%20passed-brightgreen)](#5-running-tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> ⚠️ **DEMO SYSTEM — All data is synthetic. Risk scores are for demonstration only and have not been validated on real financial transactions. Do not use for live fraud decisions.**

---

## Problem Statement

Payment fraud causes significant annual losses for merchants and card issuers. Most deployed fraud models return a binary decision or an opaque score, giving analysts no way to understand why a transaction was flagged, verify whether the reasoning makes sense, or build confidence in the system's recommendations.

RiskLens AI demonstrates a complete explainable fraud-risk pipeline:

- A transaction arrives → features are extracted → two ML models score it → the higher-scoring model's prediction is explained in plain English using actual feature contributions
- Flagged transactions flow into a structured investigation queue with a persistent, immutable audit trail
- Analysts can simulate the cost trade-offs of tightening or loosening the detection threshold before committing to a change

---

## Key Features

| Feature | Status | Description |
|---|---|---|
| Risk scoring | ✅ Implemented | 0–100 score mapped from model probability, classified as low / medium / high |
| Explainable predictions | ✅ Implemented | Feature contributions derived from model coefficients (LR) or feature importances (RF) — not heuristic labels |
| Transaction analysis | ✅ Implemented | Manual form input and CSV batch upload (up to 10,000 rows, 10 MB) |
| Investigation workbench | ✅ Implemented | Searchable queue, analyst notes, state machine, immutable audit history |
| Risk simulator | ✅ Implemented | Threshold slider, confusion-matrix breakdown, estimated review and fraud-loss costs |
| Model evaluation | ✅ Implemented | Precision, recall, F1, PR-AUC, confusion matrix — computed on held-out 20% test set |
| Data drift monitor | ✅ Implemented | PSI per feature, recent vs training distribution |
| Dashboard | ✅ Implemented | KPI cards, 14-day trend, risk distribution, category breakdown |

---

## Technology Stack

Versions are pinned in `backend/requirements.txt` and `frontend/package.json` and were verified against the running project.

**Backend**

| Package | Version | Role |
|---|---|---|
| Python | 3.14.2 (tested) | Runtime |
| FastAPI | 0.143.1 | Web framework |
| Uvicorn | 0.54.0 | ASGI server |
| SQLAlchemy | 2.1.4 | ORM + SQLite |
| Pydantic v2 | 2.13.4 | Request/response validation |
| pydantic-settings | 2.16.0 | Environment config |
| scikit-learn | 1.9.0 | Logistic Regression, Random Forest |
| pandas | 2.3.3 | Data manipulation |
| NumPy | 2.4.0 | Numerical operations |
| scipy | 1.18.0 | Statistical utilities |
| imbalanced-learn | 0.14.2 | Compatibility dependency |
| joblib | 1.5.3 | Model serialisation |
| pytest | 9.1.1 | Test runner |

> All packages have prebuilt `cp314-cp314-win_amd64` wheels. No Cython compilation is required on Python 3.14 with these pinned versions. The original pins (`scikit-learn==1.4.2`, `numpy==1.26.4`) predated Python 3.14 and did not have cp314 wheels; see `requirements.txt` for the full explanation.

**Frontend**

| Package | Version | Role |
|---|---|---|
| React | ^18.3.1 | UI framework |
| TypeScript | ^5.4.5 | Type safety |
| Vite | ^5.2.11 | Dev server + bundler |
| Recharts | ^2.12.7 | Charts |
| React Router | ^6.23.1 | Client-side routing |
| Axios | ^1.7.2 | HTTP client |

---

## Architecture

```
risklens-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI entry point + lifespan startup
│   │   ├── config.py            Pydantic-settings environment config
│   │   ├── database.py          SQLAlchemy engine + session factory
│   │   ├── models/
│   │   │   ├── transaction.py   Transaction ORM model (unique transaction_id)
│   │   │   ├── investigation.py Investigation + AnalystNote ORM models
│   │   │   └── audit.py         AuditLog ORM model (append-only)
│   │   ├── schemas/
│   │   │   ├── transaction.py   Pydantic v2 input/output schemas
│   │   │   ├── investigation.py Investigation schemas
│   │   │   └── dashboard.py     Dashboard, simulator, evaluation schemas
│   │   ├── routers/
│   │   │   ├── transactions.py  POST /analyze, POST /upload-csv, GET list/detail
│   │   │   ├── dashboard.py     GET /stats, GET /charts
│   │   │   ├── investigations.py GET list, POST review/notes, GET audit
│   │   │   ├── simulator.py     GET thresholds, POST simulate
│   │   │   └── model.py         GET evaluation/monitoring, POST train
│   │   ├── ml/
│   │   │   ├── pipeline.py      Training pipeline — strict 80/20 stratified split
│   │   │   ├── features.py      14-feature FraudFeatureTransformer
│   │   │   ├── predictor.py     Inference engine with thread-safe model cache
│   │   │   ├── explainer.py     Evidence-based explanation generator
│   │   │   └── evaluator.py     Loads saved metrics for API responses
│   │   └── services/
│   │       ├── risk_engine.py   Threshold classification + cost simulation
│   │       ├── audit.py         Immutable audit-log service
│   │       └── drift_monitor.py PSI-based data drift detection
│   ├── data/
│   │   ├── generate_data.py     Synthetic dataset generator (documented below)
│   │   ├── fraud_dataset.csv    Generated training dataset — 20 k rows, synthetic
│   │   └── sample.csv           13-row demo file for quick UI testing
│   ├── models/                  Pre-trained model artifacts (≤ 180 KB each)
│   │   ├── best_model.pkl
│   │   ├── lr_model.pkl
│   │   ├── rf_model.pkl
│   │   ├── model_metadata.json
│   │   └── reference_stats.json
│   ├── scripts/
│   │   ├── train.py             Full training CLI script
│   │   └── smoke_test.py        Live API smoke test (requires running server)
│   ├── tests/                   77 automated tests
│   ├── .env.example
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Dashboard.tsx
    │   │   ├── TransactionAnalysis.tsx
    │   │   ├── InvestigationWorkbench.tsx
    │   │   ├── RiskSimulator.tsx
    │   │   └── ModelEvaluation.tsx
    │   ├── components/
    │   │   ├── common/          Card, Badge, Button, Loading, ErrorDisplay, RiskScore
    │   │   └── layout/          Layout, Sidebar
    │   ├── api/client.ts        Typed Axios client for all endpoints
    │   ├── hooks/useApi.ts      Generic data-fetching hook
    │   └── types/index.ts       TypeScript interfaces matching backend schemas
    ├── index.html
    ├── vite.config.ts           Dev server port 3000, proxy /api → localhost:8000
    ├── package.json
    └── tsconfig.json
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | **3.14** | All pinned packages have cp314 wheels; earlier versions may require source builds |
| Node.js | 18 or later | Tested on 24.16.0 |
| Git | any recent | For cloning |

---

## Local Setup

### 1 — Clone

```bash
git clone https://github.com/Kavyapriya926/risklens-ai.git
cd risklens-ai
```

### 2 — Backend

All commands must be run from inside the `backend/` directory so relative paths (`./models`, `./data`) resolve correctly.

```powershell
cd backend

# Install all dependencies (prebuilt wheels, no compilation needed on Python 3.14)
pip install -r requirements.txt

# Copy the environment template — edit values if needed
copy .env.example .env

# The repository already includes pre-trained models in backend/models/.
# To regenerate the dataset and retrain from scratch (optional):
python data/generate_data.py          # writes backend/data/fraud_dataset.csv
python scripts/train.py               # trains both models, saves to backend/models/

# Start the API server (must be run from backend/)
python -m uvicorn app.main:app --reload --port 8000
```

**API available at:** http://localhost:8000  
**Swagger UI:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc

### 3 — Frontend

```powershell
cd frontend
npm install
npm run dev
```

**App available at:** http://localhost:3000

The Vite development server is configured on port 3000 (`vite.config.ts: server.port: 3000`) and proxies all `/api/*` and `/health` requests to `http://localhost:8000`. Both servers must be running simultaneously.

---

## Environment Variables

Defined in `.env.example` (safe example values only — no secrets):

```env
SECRET_KEY=change-me-in-production-use-a-long-random-string
DATABASE_URL=sqlite:///./risklens.db
MODEL_DIR=./models
DATA_DIR=./data
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

Copy to `.env` before starting the backend. The `.env` file is in `.gitignore` and will never be committed.

---

## API Endpoints

Full interactive documentation is available at http://localhost:8000/docs.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service health check |
| POST | `/api/transactions/analyze` | Analyze a single transaction; returns risk score + explanation |
| POST | `/api/transactions/upload-csv` | Batch CSV upload (up to 10,000 rows, 10 MB) |
| GET | `/api/transactions` | List transactions with optional `risk_level` filter |
| GET | `/api/transactions/{id}` | Full detail for one transaction |
| GET | `/api/dashboard/stats` | KPI metrics (total, high-risk, fraud rate, avg score) |
| GET | `/api/dashboard/charts` | Chart data (risk distribution, daily trends, category breakdown) |
| GET | `/api/investigations` | Investigation queue (filterable by status, priority, search) |
| POST | `/api/investigations/{id}/review` | Analyst action: review / escalate / close / reopen |
| POST | `/api/investigations/{id}/notes` | Add an analyst note |
| GET | `/api/investigations/{id}/audit` | Full immutable audit history |
| GET | `/api/simulator/thresholds` | Current threshold configuration |
| POST | `/api/simulator/simulate` | Simulate threshold change — returns confusion matrix + cost breakdown |
| GET | `/api/model/evaluation` | Model metrics report (from held-out test set) |
| GET | `/api/model/monitoring` | Data drift report + model version info |
| POST | `/api/model/train` | Trigger background re-training |

**Duplicate transaction IDs:** `POST /api/transactions/analyze` returns **HTTP 409 Conflict** if the supplied `transaction_id` already exists. Omit `transaction_id` to have the server generate a UUID automatically.

---

## Running Tests

Tests must be run from the `backend/` directory.

```powershell
cd backend
python -m pytest tests/ -v
```

**Verified result (Python 3.14.2, pytest 9.1.1):**

```
77 passed, 0 failed, 1 warning
```

The warning is a deprecation notice from starlette's `TestClient` — it does not affect test results.

| Test file | Count | Coverage |
|---|---|---|
| `test_api.py` | 25 | All API endpoints, CSV upload, investigation workflow, duplicate ID 409 handling, session rollback after conflict |
| `test_audit.py` | 6 | Immutable audit log, chronological ordering, before/after state snapshots |
| `test_ml_pipeline.py` | 9 | Dataset generation, feature transformer, 80/20 split integrity, no training-data leakage into test evaluation |
| `test_risk_engine.py` | 17 | `classify_risk`, threshold simulation, cost calculation, boundary conditions |
| `test_validation.py` | 13 | Input sanitisation, injection prevention, all boundary and edge cases |

---

## Dataset

All data is **synthetically generated** by `backend/data/generate_data.py`. No real transaction data is used anywhere in this project.

### Generation approach

`generate_synthetic_dataset()` creates two populations from different statistical distributions:

| Feature | Legitimate | Fraudulent |
|---|---|---|
| `merchant_category` | All 15 categories (realistic weights) | Restricted to 6: jewelry, gaming, financial_services, online_marketplace, electronics, travel |
| `hour_of_day` | Business-hours weighted (peaks 9 AM–6 PM) | Forced to {0, 1, 2, 3, 4, 23} |
| `is_international` | 8% probability | 55% probability |
| `is_new_merchant` | 10% probability | 65% probability |
| `card_age_days` | 30–3,650 days | 1–90 days |
| `velocity_24h` | 1–3 transactions | 5–19 transactions |
| `distance_from_home_km` | Exponential mean ≈ 20 km | Exponential mean ≈ 400 km |

### Why metrics on this data are not meaningful for real-world performance

The fraud label **directly determines** the distribution of every feature during generation. For example:

- `is_high_risk_category` (a training feature) maps exactly the 4 categories that appear only in fraudulent rows
- `is_night` (hours 0–6 AM) captures the forced fraud hours almost exclusively
- `is_international` and `is_new_merchant` have non-overlapping rates (55% vs 8%, 65% vs 10%)
- `velocity_24h` ranges do not overlap (fraud: 5–19, legit: 1–3)

This is not traditional target leakage (the `is_fraud` column is not a training feature), and the preprocessing transformer is fit only on training data (verified in `pipeline.py`). However, the synthetic construction makes the classification task **close to trivially easy** — a model can learn near-perfect separation by combining a few features that have been engineered to reflect the fraud-generation rules exactly.

**Reported metrics on this synthetic dataset (held-out 20% test set):**

| Model | Precision | Recall | F1 | PR-AUC | FPR |
|---|---|---|---|---|---|
| Logistic Regression | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| Random Forest | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |

These results are **reproducible and accurately reported** from the held-out test set. They reflect the artificial separability of the synthetic data, not real-world fraud detection capability. The `model_metadata.json` disclaimer states this explicitly.

There is no data leakage from the test set into training: `train_test_split` is called before any `fit()`, and the `FraudFeatureTransformer` (which computes per-category amount z-scores) is fit only on `X_train`.

---

## ML Pipeline

### Feature engineering (14 features)

| Feature | Derivation |
|---|---|
| `amount_log` | `log1p(amount)` |
| `amount_zscore` | `(amount − category_mean) / category_std`, clamped to ±10 |
| `hour_sin`, `hour_cos` | Cyclic encoding: `sin/cos(2π × hour / 24)` |
| `day_sin`, `day_cos` | Cyclic encoding: `sin/cos(2π × day / 7)` |
| `is_international` | Pass-through binary |
| `is_new_merchant` | Pass-through binary |
| `velocity_24h_log` | `log1p(velocity_24h)` |
| `card_age_days_log` | `log1p(card_age_days)`, 0 if missing |
| `distance_log` | `log1p(distance_from_home_km)`, 0 if missing |
| `is_night` | `1` if `0 ≤ hour < 6` |
| `is_weekend` | `1` if `day_of_week ≥ 5` |
| `is_high_risk_category` | `1` if category ∈ {gaming, financial_services, online_marketplace, jewelry} |

### Models

**Logistic Regression** — linear baseline trained with `class_weight="balanced"`, `C=0.1`, `max_iter=1000`. Explanations use signed `coefficient × scaled_feature_value` per feature.

**Random Forest** — 100 estimators, `max_depth=8`, `class_weight="balanced"`, `min_samples_leaf=10`, `n_jobs=1`. Explanations use global `feature_importances_` with a value-based sign heuristic.

> For production-grade per-prediction explanations, replace the RF explanation with SHAP `TreeExplainer`.

### Training procedure

1. Stratified 80/20 split (`random_state=42`) — test set is locked before any preprocessing
2. `FraudFeatureTransformer.fit()` called **only on `X_train`** — no leakage into test evaluation
3. For Logistic Regression: features are additionally passed through `StandardScaler` (also fit on `X_train` only)
4. Both models trained, both evaluated on the same held-out test set
5. Best model selected by F1-score on test set; all three artifacts saved (`best_model.pkl`, `lr_model.pkl`, `rf_model.pkl`)
6. Reference statistics for drift detection computed from `X_train` features only

---

## Limitations and Responsible Use

1. **Synthetic data only.** The system has never been evaluated on real transaction data. Reported metrics reflect synthetic-data separability, not real-world fraud detection accuracy.

2. **RF explanations are approximate.** Random Forest explanations use global feature importances, which measure average contribution across all trees, not the contribution for a specific prediction. For accurate per-prediction explanations on tree models, integrate `shap` with `TreeExplainer`.

3. **No authentication or authorisation.** The API has no login layer. Do not expose the backend to any network without adding authentication (e.g., OAuth2/JWT).

4. **SQLite database.** Suitable for local development only. Production deployments require PostgreSQL with proper connection pooling.

5. **In-process re-training.** The `POST /api/model/train` endpoint runs training as a FastAPI `BackgroundTask` in the same process. Production systems should use a dedicated worker (Celery, RQ).

6. **No rate limiting, no horizontal scaling.** Single-process, single-machine deployment only.

7. **Duplicate transaction IDs return 409, not 500.** The router checks for existing IDs before attempting the insert and rolls back cleanly on conflict. Do not supply a fixed `transaction_id` in repeated Swagger UI "Try it out" calls.

---

## Security

- Pydantic v2 validates and sanitises every input field (amounts, hours, categories, transaction IDs)
- SQLAlchemy ORM uses parameterised queries — no raw SQL
- CSV uploads: file-type check, 10 MB size cap, 10,000-row limit, UTF-8 encoding required
- Environment secrets via `.env` (never committed; `.env.example` contains only safe placeholder values)
- No real payment operations are performed or blocked by this system

---

## License

MIT — see [LICENSE](LICENSE).

---

*Built for the Razorpay AI Buildathon — AI Risk Manager Track.*  
*GitHub: https://github.com/Kavyapriya926/risklens-ai*
