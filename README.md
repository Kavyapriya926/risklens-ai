# RiskLens AI — Explainable Payment Fraud Risk Management System

> **Razorpay AI Buildathon — AI Risk Manager Track**

[![Python](https://img.shields.io/badge/Python-3.14-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![Tests](https://img.shields.io/badge/tests-77%20passed-brightgreen)](#testing)

> ⚠️ **DEMO SYSTEM — Trained on synthetic data. Risk scores are for demonstration purposes only and are not validated for real-world financial decisions.**

---

## Problem Statement

Payment fraud causes billions in annual losses. Fraud detection models are often black boxes — they flag transactions without explaining why, making it impossible for analysts to validate, appeal, or learn from their decisions. RiskLens AI addresses this by combining ML-based risk scoring with evidence-based explanations, a structured investigation workflow, and tools to understand the cost trade-offs of different detection thresholds.

---

## Key Features

| Feature | Description |
|---|---|
| **Risk Scoring** | Score 0–100 per transaction with low / medium / high classification |
| **Explainable Predictions** | Evidence-based feature contributions derived from model coefficients — not arbitrary labels |
| **Transaction Analysis** | Manual form input or CSV batch upload (up to 10,000 rows) |
| **Investigation Workbench** | Searchable queue, analyst notes, state machine (open → reviewed → escalated → closed), audit trail |
| **Risk Simulator** | Adjust thresholds and immediately see impact on fraud detection rate, false positives, and estimated costs |
| **Model Evaluation** | Precision, recall, F1, PR-AUC, confusion matrix — all computed on a genuinely held-out test set |
| **Data Drift Monitor** | PSI-based feature drift report comparing recent transactions to training distribution |
| **Professional Dashboard** | KPI cards, 14-day trend chart, risk distribution, category breakdown |

---

## Technology Stack

```
Backend                          Frontend
───────────────────────────────  ────────────────────────────────
Python 3.14                      React 18 + TypeScript
FastAPI 0.143                    Vite 5
SQLAlchemy 2.1 + SQLite          Recharts 2.12
Pydantic v2                      React Router 6
scikit-learn 1.9 (RF + LR)       Axios
pandas 2.3 / numpy 2.4
joblib / scipy
pytest 9 (77 tests)
```

---

## Architecture

```
risklens-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI entry point + lifespan
│   │   ├── config.py            Environment-variable configuration
│   │   ├── database.py          SQLAlchemy engine + session
│   │   ├── models/              ORM: Transaction, Investigation, AuditLog
│   │   ├── schemas/             Pydantic v2 request/response models
│   │   ├── routers/             5 API routers (transactions, dashboard,
│   │   │                          investigations, simulator, model)
│   │   ├── ml/
│   │   │   ├── pipeline.py      Training pipeline (80/20 stratified split)
│   │   │   ├── features.py      14 engineered features + FraudFeatureTransformer
│   │   │   ├── predictor.py     Inference engine with model caching
│   │   │   ├── explainer.py     Evidence-based explanation generator
│   │   │   └── evaluator.py     Loads saved metrics for API responses
│   │   └── services/
│   │       ├── risk_engine.py   Threshold classification + cost simulation
│   │       ├── audit.py         Immutable audit log service
│   │       └── drift_monitor.py PSI-based data drift detection
│   ├── data/
│   │   ├── generate_data.py     Synthetic dataset generator
│   │   ├── fraud_dataset.csv    Generated training dataset (20k rows, synthetic)
│   │   └── sample.csv           13-row demo file for quick testing
│   ├── models/                  Trained model artifacts (pkl + metadata)
│   ├── scripts/
│   │   ├── train.py             Full training script
│   │   └── smoke_test.py        Live API smoke test
│   ├── tests/                   77 automated tests
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/               Dashboard, TransactionAnalysis, InvestigationWorkbench,
        │                          RiskSimulator, ModelEvaluation
        ├── components/          Layout, Sidebar, Card, RiskScore gauge
        ├── api/client.ts        Typed Axios API client
        ├── hooks/useApi.ts      Data-fetching hook
        └── types/index.ts       TypeScript interfaces
```

---

## Prerequisites

- **Python 3.11+** (tested on 3.14.2)
- **Node.js 18+** (tested on 24.16.0)
- **Git**

---

## Local Setup

### 1 — Clone

```bash
git clone https://github.com/Kavyapriya926/risklens-ai.git
cd risklens-ai
```

### 2 — Backend

```powershell
cd backend

# Install dependencies (all have prebuilt wheels — no source compilation)
pip install -r requirements.txt

# Copy environment config
copy .env.example .env

# The repo includes pre-trained model files in backend/models/.
# To retrain from scratch (optional):
python data/generate_data.py
python scripts/train.py

# Start the API server
python -m uvicorn app.main:app --reload --port 8000
```

API available at: **http://localhost:8000**  
Swagger UI: **http://localhost:8000/docs**

### 3 — Frontend

```powershell
cd frontend
npm install
npm run dev
```

App available at: **http://localhost:3000**

> The Vite dev server proxies all `/api/*` requests to `localhost:8000` automatically.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/transactions/analyze` | Analyze a single transaction |
| POST | `/api/transactions/upload-csv` | Batch CSV upload (up to 10,000 rows) |
| GET | `/api/transactions` | List transactions with filters |
| GET | `/api/transactions/{id}` | Transaction detail |
| GET | `/api/dashboard/stats` | KPI metrics |
| GET | `/api/dashboard/charts` | Chart data |
| GET | `/api/investigations` | Investigation queue |
| POST | `/api/investigations/{id}/review` | Analyst review action |
| POST | `/api/investigations/{id}/notes` | Add analyst note |
| GET | `/api/investigations/{id}/audit` | Full audit history |
| POST | `/api/simulator/simulate` | Run threshold simulation |
| GET | `/api/model/evaluation` | Model metrics report |
| GET | `/api/model/monitoring` | Drift report + version info |
| POST | `/api/model/train` | Trigger background re-training |

Full interactive documentation at `/docs` (Swagger UI) or `/redoc`.

---

## Testing

```powershell
cd backend
python -m pytest tests/ -v
```

**Result: 77 passed, 0 failed**

| Test file | Tests | Coverage |
|---|---|---|
| `test_api.py` | 25 | All endpoints, CSV upload, investigation workflow, duplicate ID handling |
| `test_audit.py` | 6 | Immutable audit log, chronological ordering, state snapshots |
| `test_ml_pipeline.py` | 9 | Feature transformer, train/test split, no data leakage, metrics |
| `test_risk_engine.py` | 17 | Risk classification, threshold simulation, cost calculation |
| `test_validation.py` | 13 | Input sanitization, injection prevention, boundary conditions |

---

## Dataset

All data is **synthetic and programmatically generated** by `backend/data/generate_data.py`.

- 20,000 transactions at 5% fraud rate
- Structure mirrors public fraud benchmarks (IEEE-CIS Fraud Detection, PaySim)
- Fraud is modelled as combinations of: high amounts, night-time hours (0–6 AM), international flag, new merchant flag, high velocity (≥5 txns/24h), large distance from home, high-risk categories (gaming, jewelry, financial_services, online_marketplace)
- **No real payment data is used anywhere in this project**

---

## ML Pipeline

### Features (14 engineered)

| Feature | Encoding |
|---|---|
| amount | log₁₊(amount), z-score within category |
| hour_of_day | Cyclic sin/cos, is_night flag (0–6 AM) |
| day_of_week | Cyclic sin/cos, is_weekend flag |
| is_international | Binary |
| is_new_merchant | Binary |
| velocity_24h | log₁₊(count) |
| card_age_days | log₁₊(days) |
| distance_from_home_km | log₁₊(km) |
| merchant_category | is_high_risk_category flag |

### Models

- **Logistic Regression** — linear baseline; explanations use signed coefficient × feature value
- **Random Forest** — 100 trees, max depth 8, balanced class weights; explanations use feature importances

### Evaluation (on held-out 20% test set, synthetic data)

```
Logistic Regression  Precision=1.000  Recall=1.000  F1=1.000  PR-AUC=1.000
Random Forest        Precision=1.000  Recall=1.000  F1=1.000  PR-AUC=1.000
```

> Perfect metrics are **expected on clearly separable synthetic data** and do not reflect real-world performance. Real-world fraud datasets typically yield F1 0.70–0.85, PR-AUC 0.75–0.90, depending on the dataset and operating threshold.

---

## Limitations & Honest Disclosures

1. **Synthetic data only** — this system has never been validated on real transaction data. Do not use it for live fraud decisions.
2. **RF explanations** — uses global feature importances, not per-prediction SHAP values. For production, integrate `shap` with `TreeExplainer`.
3. **No authentication** — the API has no login layer. Add JWT/OAuth2 before any network exposure.
4. **SQLite** — fine for local demo; production requires PostgreSQL with connection pooling.
5. **In-process training** — re-training runs in the FastAPI process via `BackgroundTasks`. Production should use Celery + Redis.
6. **Single-node** — no horizontal scaling, no message queue, no rate limiting.

---

## Security Notes

- Input validation via Pydantic v2 with strict constraints on all fields
- SQL injection prevented by SQLAlchemy ORM parameterized queries
- Duplicate transaction IDs return HTTP 409 with rollback (no 500 / broken session state)
- CSV uploads: type validation, size limit (10 MB), row limit (10,000), UTF-8 only
- Secrets via `.env` file — never hardcoded. See `.env.example`
- No real payments are executed or blocked by this system

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

*Built for the Razorpay AI Buildathon — AI Risk Manager track.*
