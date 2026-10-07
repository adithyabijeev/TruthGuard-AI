# TruthGuard AI

TruthGuard is a **Fraud Intelligence & Prevention Engine**. It is designed to detect fraud hidden inside otherwise legitimate-looking information by analyzing context, impersonation, suspicious actions, payment/data requests, urgency, and infrastructure signals.

It is intentionally **not** positioned as a generic fake-news detector or fact-checker.

## Included

- React + Vite frontend
- Django + Django REST Framework backend
- PostgreSQL via Docker Compose
- Fraud analysis engine with explainable signals
- Fraud DNA extraction
- Attack graph generation
- Campaign/variant linking
- Risk scoring and prevention actions
- Scan history
- Responsive dashboard
- Health endpoint
- Seed/demo API endpoint

## Run with Docker

Requirements: Docker Desktop.

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- API: http://localhost:8000/api/
- Health: http://localhost:8000/api/health/
- Django admin: http://localhost:8000/admin/

## Run without Docker

### Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

For local SQLite without PostgreSQL:

```powershell
$env:USE_SQLITE="1"
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Create `frontend/.env` if the API is not on the default URL:

```env
VITE_API_URL=http://localhost:8000/api
```

## Core API

### POST `/api/analyze/`

```json
{
  "title": "Urgent account verification",
  "content": "Your bank account will be blocked today. Verify immediately at http://example.com",
  "source": "SMS"
}
```

Returns a structured analysis including risk score, severity, fraud DNA, signals, attack graph, campaign fingerprint, and prevention actions.

### GET `/api/scans/`

Returns recent scans.

### GET `/api/stats/`

Returns dashboard statistics.

### GET `/api/health/`

Returns service health.

## Important production work

Before public deployment, replace the development secret, configure PostgreSQL credentials, restrict CORS, add authentication/rate limiting, add a real threat-intelligence provider, use HTTPS, configure trusted hosts, and move analysis jobs to a queue such as Celery/RQ.
