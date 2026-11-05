# Vytal

Health analytics for everyday smartwatch users.

Vytal collects health data from affordable smartwatches via Google Fit and generates personalized indicators — starting with the **Daily Readiness Score** — with actionable recommendations.

---

## Architecture

```
Mobile App (React Native)
       │
       ▼
API Gateway (FastAPI)
       │
       ├── Ingest Service
       ├── Process Service  (Apache Beam pipelines)
       └── Reports Service  (Daily Readiness Score + insights)
       │
       ▼
Health Data Connector Hub   ← adapters per health provider
       │
       ▼
Cloud Abstraction Layer     ← adapters per cloud provider (local | GCP | AWS | Azure)
```

### Stack

| Layer | Technology |
|-------|------------|
| Mobile | React Native (Expo) |
| API Gateway | FastAPI (Python 3.11+) |
| Pipelines | Apache Beam (DirectRunner locally, Dataflow on GCP) |
| Local warehouse | SQLite (via aiosqlite) |
| Cloud warehouse | BigQuery |
| IaC | Terraform |
| CI/CD | GitHub Actions |

---

## Project Structure

```
Vytal/
├── backend/                  ← FastAPI app
│   ├── app/
│   │   ├── api/v1/           ← routers (connect, health-data, readiness)
│   │   ├── services/         ← business logic
│   │   ├── repositories/     ← data access
│   │   ├── domain/           ← HealthMetric interface + implementations
│   │   ├── adapters/
│   │   │   ├── cloud/        ← StorageProvider, WarehouseProvider (local + GCP)
│   │   │   └── connectors/   ← HealthDataProvider (Google Fit + future providers)
│   │   └── config/           ← settings + cloud config loader
│   ├── tests/
│   ├── config.yaml           ← active cloud provider (local | gcp)
│   └── requirements.txt
├── pipelines/                ← Apache Beam pipelines
│   ├── transforms/           ← reusable DoFns
│   ├── pipeline_raw_normalized_health.py
│   └── pipeline_normalized_readiness_score.py
├── mobile/                   ← React Native app (coming soon)
├── infrastructure/
│   ├── docker-compose.yml
│   ├── docker/
│   └── terraform/
└── docs/
    ├── prd.md
    └── architecture/
```

---

## Local Setup

Para executar o MVP completo com SQLite, web e Android, veja [o guia local](docs/LOCAL-MVP.md) e [as evidências E2E](docs/MVP-LOCAL-REPORT.md). O launcher mantém portas/configuração consistentes e oferece dados sintéticos por conta.


### Prerequisites

- Python 3.11+
- A Google Cloud project with the **Fitness API** enabled
- OAuth 2.0 credentials (Web application type)

### 1. Clone and install

```bash
git clone <repo-url>
cd Vytal/backend
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/connect/google_fit/callback
```

For local use only, omitted signing keys are generated randomly on startup. Set private
`SECRET_KEY` and `JWT_SECRET_KEY` values if local sessions must survive restarts.
Never commit them. `.env` cannot choose the runtime environment; select it explicitly
in the startup command below.

### 3. Configure cloud provider

`config.yaml` defaults to `local` (SQLite + filesystem). No changes needed to run locally.

```yaml
cloud:
  provider: local   # change to "gcp" for production
```

### 4. Start the API

```bash
ENVIRONMENT=local uvicorn app.main:app --reload
```

API running at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

For tests: `ENVIRONMENT=test GOOGLE_CLIENT_ID=synthetic GOOGLE_CLIENT_SECRET=synthetic pytest`.
For production requirements, frontend endpoints, demo opt-in and validation evidence,
see [PKG-03 secure configuration](docs/egm/10-pkg-03-secure-configuration.md).

---

## Google Fit OAuth Setup

Before syncing data, the user must authorize Vytal to access their Google Fit data.

### Step 1 — Get the authorization URL

```bash
GET /api/v1/connect/google_fit/auth-url?user_id=user-123&redirect_uri=http://localhost:8000/api/v1/connect/google_fit/callback
```

Response:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "user-123:nonce:signature"
}
```

Open `auth_url` in a browser, authorize, and copy the `code` from the redirect URL.

### Step 2 — Exchange code for token

```bash
POST /api/v1/connect/google_fit/callback
{
  "code": "4/0AX4...",
  "state": "user-123:nonce:signature",
  "redirect_uri": "http://localhost:8000/api/v1/connect/google_fit/callback"
}
```

### Step 3 — Sync health data

```bash
POST /api/v1/health-data/sync
{
  "user_id": "user-123",
  "provider": "google_fit",
  "start_date": "2024-01-10",
  "end_date": "2024-01-15"
}
```

### Step 4 — Get Daily Readiness Score

```bash
GET /api/v1/readiness/user-123?date=2024-01-15
```

Response:
```json
{
  "user_id": "user-123",
  "date": "2024-01-15",
  "readiness_score": 74.5,
  "readiness_category": "moderate",
  "contributions": {
    "sleep": 80.0,
    "heart_rate": 75.0,
    "activity": 70.0,
    "stress": null
  },
  "insight_text": "Você está bem recuperado. Um treino moderado ou cardio é recomendado."
}
```

---

## Running Pipelines Standalone

Pipelines can also be triggered independently (useful for backfills):

```bash
# Normalize raw data
python pipelines/pipeline_raw_normalized_health.py \
  --user_id=user-123 \
  --start_date=2024-01-01 \
  --end_date=2024-01-07

# Calculate Daily Readiness Score
python pipelines/pipeline_normalized_readiness_score.py \
  --user_id=user-123 \
  --start_date=2024-01-01 \
  --end_date=2024-01-07
```

---

## Running with Docker

```bash
cd infrastructure
docker-compose up
```

API available at `http://localhost:8000`. Data persisted in a Docker volume.

---

## Running Tests

```bash
cd backend
pytest --cov=app tests/
```

---

## Switching to GCP

1. Fill in `config.yaml`:
```yaml
cloud:
  provider: gcp
gcp:
  project: your-gcp-project
  region: us-central1
  storage_bucket: your-bucket
  bigquery_dataset: vytal
  dataflow_temp: gs://your-bucket/temp
```

2. Add GCP dependencies:
```bash
pip install google-cloud-storage google-cloud-bigquery
```

3. Authenticate:
```bash
gcloud auth application-default login
```

---

## Adding a New Health Data Provider

1. Create `backend/app/adapters/connectors/your_provider.py` implementing `HealthDataProvider`
2. Register in `backend/app/adapters/connectors/factory.py`
3. Add OAuth scopes and API mapping in the adapter

See [docs/architecture/interfaces.md](docs/architecture/interfaces.md) for the full interface contract.

---

## Daily Readiness Score

Score from 0 to 100 calculated daily per user:

| Score | Category | Recommendation |
|-------|----------|----------------|
| 80–100 | Intense | Ready for intense training |
| 50–79 | Moderate | Moderate training or cardio |
| 30–49 | Light | Light activity recommended |
| 0–29 | Rest | Rest and recovery |

**Weights:** Sleep 40% · Heart Rate 30% · Activity Load 20% · Stress 10%  
Stress weight is redistributed when unavailable (most budget watches don't measure it).

---

## Agent Team

This project is developed by a team of specialized AI agents. See [cloude-agents/AGENTS.md](../cloude-agents/AGENTS.md) for the team structure and skills.
