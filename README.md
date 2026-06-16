# WinWin Law Team — MLM Affiliate Platform

A full-stack multi-level marketing affiliate platform for selling WinWin Law subscriptions.

## Stack

- **Frontend**: React 18 + Vite + TypeScript + Tailwind CSS + TanStack Query
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + JWT auth

## Setup

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
npm install
npm run dev        # http://localhost:5173
```

Set `VITE_API_URL=http://localhost:8001` in `.env.local` if the backend runs on a different port.

## Features

- **Landing page** — public marketing page with commission tiers
- **Affiliate registration** with referral code tracking
- **Dashboard** — stats cards + copyable referral link
- **Team page** — downline members grouped by level (L1/L2/L3…)
- **Earnings page** — commission history + payout request form
- **Admin panel** — manage affiliates, approve/reject payouts, add manual commissions

## Commission Structure

| Level | Who | Rate |
|-------|-----|------|
| L1 | Direct referrals | 20% |
| L2 | Referrals' referrals | 10% |
| L3 | 3rd-degree | 5% |

## Creating an Admin User

After registering normally, run SQL to promote a user:

```sql
UPDATE affiliates SET is_admin = true WHERE email = 'admin@example.com';
```

## API Endpoints

- `POST /api/auth/register` — create account (optional `referral_code`)
- `POST /api/auth/login` — get JWT token
- `GET /api/affiliate/me` — profile
- `GET /api/affiliate/stats` — earnings stats
- `GET /api/affiliate/team` — downline tree
- `GET /api/affiliate/earnings` — commission history
- `POST /api/affiliate/payout` — request payout
- `GET /api/admin/stats` — admin stats
- `GET /api/admin/affiliates` — all affiliates
- `GET/PUT /api/admin/payouts` — manage payout requests
- `POST /api/admin/commission` — add manual commission
- `POST /api/admin/simulate-subscription` — test MLM tree
