# VERIQ AI
**Trust every document. Validate every application.**

A local-first MVP for application intake, document screening, deterministic validation, configurable illustrative compliance rules, human review, audit events, and report export.

## What's implemented
- React + TypeScript + Vite frontend with a responsive dark glassmorphism design.
- FastAPI API under `/api/v1`, SQLAlchemy models, SQLite local database, upload storage, seed data.
- Application creation/list/detail, document upload, verification pipeline, review decisions, audit log, compliance rules, CSV report export.
- Deterministic checks: required document presence, file type/size, extracted text availability, required fields, expiry-like date indicators, and matching applicant names across extracted text when possible.
- Text extraction for `.txt` and text-based PDFs when `pypdf` is installed. Other formats are stored and clearly marked as not parsed.
- Synthetic demo records and explicit demo-mode labeling.
- Backend pytest tests.

## Important limits
This is an educational MVP, not a production compliance product. OCR/AI provider integrations are interfaces/placeholders only; no external AI service is called. A file passing checks is **not** proof of authenticity. Compliance rules are illustrative and do not establish legal compliance. Authentication is demo-only and must be replaced before deployment. Do not upload real sensitive documents.

## Requirements
- Python 3.10+
- Node.js 20+
- npm

## Run locally
### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; on macOS/Linux use: cp .env.example .env
python -m app.seed
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

### 2. Frontend
In another terminal:
```bash
cd frontend
npm install
npm run dev
```
Open the Vite URL printed in the terminal. The frontend proxies `/api` to `http://127.0.0.1:8000`.

## Test
```bash
cd backend
pip install -r requirements.txt
pytest -q
```

## Database and uploads
Local development uses SQLite at `backend/veriq.db` and stores files under `backend/storage/`. PostgreSQL is supported by setting `DATABASE_URL` to a PostgreSQL SQLAlchemy URL. Alembic configuration and an initial migration are included; the app also creates tables on startup for a frictionless local demo.

## Configuration
Copy `.env.example` to `.env`. Set `DATABASE_URL` for PostgreSQL if available. Never commit secrets. File upload limit defaults to 10 MB.

## Suggested next steps
1. Replace demo authentication with OAuth/OIDC and role-based authorization.
2. Add isolated malware scanning and private object storage.
3. Integrate a real OCR engine such as Tesseract or a managed OCR provider.
4. Define approved policy profiles with legal/compliance owners.
5. Add retention/deletion jobs, rate limiting, and security review before production.
