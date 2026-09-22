# Broke-Proof

**AI Spending Controller for students** — predicts when a user will run out of money, computes a live Safe-to-Spend/Day number, saves round-ups into a protected jar, detects recurring debits, and intervenes when a purchase is likely to break the budget.

This repository implements the product described in the supplied final specification as a working full-stack MVP.

## What is included

- **Broke Date Prediction** using the specified 60% recent-7-day + 40% full-period discretionary spend heuristic.
- **Safe-to-Spend/Day** recalculated from the current spendable balance and days left in the active income cycle.
- **Round-Up Savings Jar** to the next ₹10, excluded from spendable money.
- **Per-Purchase Overspend Nudges** with `Log anyway` and `Auto-trim tomorrow` actions.
- **No-Spend Weekend** controller mode that applies a near-zero Friday–Sunday cap.
- **Visible Learn Stat** showing suggestion acceptance rate and estimated days gained.
- **Subscription / recurring-expense detection** using repeated merchant cadence, amount consistency, and fixed-category signals.
- **Manual transaction input** with merchant-category memory.
- **SMS Paste Parser** with batch parsing, regex-first extraction and optional LLM fallback.
- **Screenshot Upload + OCR** using Tesseract, followed by the same extraction pipeline and a mandatory review step.
- **JWT authentication** with access + refresh tokens and PBKDF2 password hashing.
- **MySQL production setup** through Docker Compose; SQLite fallback for zero-setup local development/tests.
- **React + Vite + Tailwind + Recharts** responsive PWA-style frontend.
- **FastAPI + SQLAlchemy** backend with OpenAPI docs.
- **Automated backend tests** for the core math, parsers and a basic API flow.

## Repository layout

```text
broke-proof/
├── backend/
│   ├── app/
│   │   ├── api/               # auth, dashboard, transactions, controller
│   │   ├── core/              # config, DB, security, auth dependency
│   │   ├── services/          # parser, OCR, categorizer, spending engine
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── main.py
│   ├── scripts/daily_recompute.py
│   ├── tests/
│   ├── seed_demo.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── lib/api.js
│   │   └── App.jsx
│   └── public/                # PWA manifest/service worker
├── docs/
│   ├── ARCHITECTURE.md
│   └── SECURITY.md
├── docker-compose.yml
└── Makefile
```

## Quick start — easiest local setup

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The default `.env.example` uses SQLite, so no database installation is required for this mode.

Open the API docs at `http://localhost:8000/docs`.

### 2. Frontend

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Full MySQL stack with Docker

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:8080`
- Backend/OpenAPI: `http://localhost:8000/docs`
- MySQL exposed locally on port `3307`

The Docker credentials are development-only. Replace them before any deployed environment.

## Deploying Frontend to Vercel

The frontend is configured for deployment on [Vercel](https://vercel.com).

### Option 1: Via Vercel Dashboard (GitHub Integration)
1. Push this repository to GitHub and go to [Vercel](https://vercel.com).
2. Click **Add New Project** and import this repository (`broke-proof`).
3. The root [`vercel.json`](file:///Users/rithwikreddy/developer/broke-proof/vercel.json) automatically configures the Vite build (`npm install --prefix frontend && npm run build --prefix frontend`, output directory: `frontend/dist`).
   - *Note*: If you choose to set the **Root Directory** setting in Vercel to `frontend`, [`frontend/vercel.json`](file:///Users/rithwikreddy/developer/broke-proof/frontend/vercel.json) is also included to handle SPA rewrites.
4. Under **Environment Variables**, configure:
   - `VITE_API_BASE`: The public URL of your deployed backend (e.g. `https://your-api.onrender.com/api` or `https://api.yourdomain.com/api`).
5. Click **Deploy**.

> [!TIP]
> Remember to add your Vercel URL to the backend's `CORS_ORIGINS` environment variable (e.g. `CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173`) so browser requests are permitted.

### Option 2: Via Vercel CLI
```bash
# Authenticate
vercel login

# Deploy preview
vercel

# Deploy to production
vercel --prod
```

## Demo account

For the non-Docker SQLite setup, seed sample student spending:

```bash
cd backend
PYTHONPATH=. python seed_demo.py
```

Then sign in with:

```text
Email:    demo@brokeproof.app
Password: demo12345
```

## SMS examples

The regex parser supports the final-spec examples directly:

```text
Rs.250.00 debited from A/c XX1234 on 07-Sep-26 to VPA swiggy@ybl. Ref No 123456789.
```

```text
INR 1,200.00 spent on your HDFC Bank Card XX5678 at AMAZON on 07-09-26.
```

For batch mode, paste multiple messages separated by a blank line.

## Optional LLM fallback

Regex parsing is always attempted first. If it fails, the backend can call an **OpenAI-compatible chat-completions endpoint** when all three environment values are provided:

```env
LLM_API_URL=
LLM_API_KEY=
LLM_MODEL=
```

If those are not configured and regex cannot parse the message, the API rejects the extraction rather than inserting uncertain money data.

## OCR

The backend uses Tesseract for screenshot OCR. Install the `tesseract` binary when running outside Docker.

macOS:

```bash
brew install tesseract
```

Ubuntu/Debian:

```bash
sudo apt-get install tesseract-ocr
```

The backend Dockerfile already installs it.

## Core formulas

### Discretionary burn rate

```text
rate = 0.6 × avg_discretionary_spend_last_7_days
     + 0.4 × avg_discretionary_spend_full_period
```

Fixed categories such as rent, tuition, utilities and subscriptions do not inflate the daily burn rate. Detected recurring expenses are projected as known future deductions.

### Safe-to-Spend

```text
safe_per_day = spendable_balance / days_remaining_in_cycle
```

When No-Spend Weekend is active, the configured Friday–Sunday cap can reduce this value further.

### Jar

```text
round_target = ceil(amount / 10) × 10
jar_contribution = round_target - amount
```

The protected jar is deducted when computing spendable balance.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Register + create first income cycle |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/refresh` | Refresh JWT pair |
| GET | `/api/dashboard` | Broke Date, Safe/day, jar, charts, Learn stats |
| POST | `/api/transactions/manual` | Manual quick-add |
| POST | `/api/transactions/parse-sms` | Regex/LLM extraction preview; supports batches |
| POST | `/api/transactions/parse-screenshot` | OCR + extraction preview |
| POST | `/api/transactions/confirm` | Confirm a parsed transaction before commit |
| GET | `/api/transactions` | Transaction history |
| POST | `/api/controller/no-spend-weekend` | Toggle No-Spend Weekend |
| POST | `/api/controller/nudges/{id}/respond` | Accept/reject overspend nudge |
| GET | `/api/controller/learn-stats` | Acceptance rate + days gained |
| GET | `/api/categories` | Category options |
| GET | `/api/health` | Health check |

## Daily recompute job

Live values are recalculated after each transaction and whenever the dashboard is read. A cron-friendly maintenance script also refreshes recurring-expense detection:

```bash
cd backend
PYTHONPATH=. python scripts/daily_recompute.py
```

Example cron entry:

```text
5 0 * * * cd /srv/broke-proof/backend && /srv/venv/bin/python scripts/daily_recompute.py
```

## Tests

```bash
cd backend
PYTHONPATH=. pytest -q
```

The current test suite covers:

- Round-up math
- Both SMS formats from the project specification
- Registration/authentication
- Transaction insertion
- Dashboard recomputation

## Important production notes

The project is a complete MVP implementation, but a public financial product still needs operational hardening. Before a real launch, use HTTPS only, encrypted managed-MySQL storage/backups, a secrets manager, rate limiting, email verification, audit/monitoring, tested data-deletion flows, and a formal DPDP/privacy review. See `docs/SECURITY.md`.

## Deliberately deferred, matching the specification

- Direct bank/UPI Account Aggregator linking
- Full ML spend-rate model
- Per-user learned nudge-framing model
- Foodie/Save vibe modes beyond No-Spend Weekend
- Shared roommate expenses
- Gamified savings streaks
