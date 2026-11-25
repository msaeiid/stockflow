# StockFlow

![CI](https://github.com/msaeiid/stockflow/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)
![Django](https://img.shields.io/badge/django-5.2%20LTS-green)
![License](https://img.shields.io/badge/license-MIT-green)

> A small-business inventory and order management system — track stock, prevent over-selling, and get low-stock alerts.

StockFlow is a full-stack web application that helps small businesses manage products, warehouses, suppliers, and customer orders. It updates stock levels as orders are placed, blocks orders that exceed available inventory, and notifies managers when an item runs low.

## Live demo

**App:** <https://stockflow.demo.karbaschian.com>
**API docs:** <https://stockflow.demo.karbaschian.com/api/docs/>

The sign-in page shows the shared demo login. All data is fictional and is reset every night.

## Features

- 📊 Dashboard with key metrics and a stock-level chart
- 📦 Products, warehouses, suppliers and categories
- 🛒 Customer orders with **atomic** multi-item stock deduction and price snapshots
- 🛡️ No over-selling: stock checks run under a row lock, so parallel orders cannot drive stock negative
- 📒 Append-only stock ledger: movements can be recorded, never edited or deleted
- 🔔 Low-stock alerts and a daily stock report (Celery; inline when Redis is absent)
- 🔐 JWT auth (with token refresh) and roles: superuser, **Manager** (edits the catalogue), **Staff** (reads the catalogue, records movements and orders)
- 📄 REST API documented with OpenAPI (Swagger UI and ReDoc, served locally)

## Tech stack

**Backend:** Python 3.12/3.13, Django 5.2 LTS, Django REST Framework, Simple JWT, drf-spectacular, PostgreSQL, Celery, Redis (optional), gunicorn, WhiteNoise
**Frontend:** React 19, TypeScript, Vite, React Router, Recharts, Axios
**Tooling:** Docker / Docker Compose, GitHub Actions, pytest, Ruff, ESLint, Prettier, pre-commit

## Architecture

```
Browser ── React SPA (built by Vite)
   │  same origin: /api/... REST + JWT
   ▼
Django + DRF (gunicorn) ── serves the SPA, static files (WhiteNoise) and the API
   │  ORM                          │
   ▼                               ▼
PostgreSQL                 Redis + Celery worker/beat (optional)
```

In production the React build is copied into the Django image and served from the same origin as the API, so there is no CORS and no API URL to configure. The frontend can still be deployed separately (set `VITE_API_URL` and `CORS_ALLOWED_ORIGINS`).

## Key engineering decisions

- **Atomic stock deduction** — an order deducts stock for all its items inside one database transaction; if any item is short, the whole order rolls back.
- **Concurrency-safe** — each movement locks its stock row (`select_for_update()`) and re-checks the available quantity under the lock; rows are locked in a stable order to avoid deadlocks.
- **Ledger, not counters** — stock only changes through `StockMovement` records, which are immutable (API, model and admin).
- **Async by design** — low-stock alerts are dispatched with `transaction.on_commit`, so they never fire for rolled-back work.
- **Graceful degradation** — without Redis the app uses an in-memory cache and runs tasks inline, so it deploys anywhere.
- **Config from the environment** — `DJANGO_PRODUCTION=True` requires a real `SECRET_KEY` and turns on the proxy SSL header and secure cookies.

## Getting started

### With Docker (development)

```bash
git clone https://github.com/msaeiid/stockflow.git
cd stockflow
cp backend/.env.example backend/.env      # then set SECRET_KEY
docker compose up --build
docker compose exec web python manage.py seed_data
```

- API: <http://localhost:8000/api/> — docs: <http://localhost:8000/api/docs/>
- Create a login: `docker compose exec web python manage.py createsuperuser`

### Without Docker

```bash
cd backend
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate          # SQLite when DATABASE_URL is not set
python manage.py seed_data        # fictional sample data (idempotent)
python manage.py createsuperuser
python manage.py runserver
```

### Frontend (development)

```bash
cd frontend
npm ci
npm run dev
```

The app runs at <http://localhost:5173> and Vite forwards `/api` to `http://127.0.0.1:8000` (change it with `VITE_PROXY_TARGET`).

### Roles

Add users to the `Manager` group to let them change products, categories, suppliers and warehouses; other signed-in users have read access and can record stock movements and orders. `seed_data` creates the `Manager` and `Staff` groups.

## Tests and code quality

```bash
cd backend
pytest                                   # SQLite; set DATABASE_URL to run on PostgreSQL
pytest --cov=inventory --cov=config      # with coverage
ruff check . && ruff format --check .

cd ../frontend
npm run lint && npm run format:check && npm run build

pre-commit install                       # once: ruff, prettier, eslint on every commit
```

The concurrency test (parallel orders cannot oversell) runs only on PostgreSQL. CI (GitHub Actions) runs the backend on Python 3.12 and 3.13 against PostgreSQL 16, the frontend on Node 22, dependency audits, and a build of the production image.

## Demo deployment

The public demo runs on a shared server behind a Caddy reverse proxy that terminates TLS for `*.demo.karbaschian.com`. This repository provides:

- `Dockerfile` — production image: builds the frontend (Node 22) and runs Django with gunicorn on port 8000 as a non-root user; the SPA, static files and API share one origin.
- `compose.demo.yml` — compose project `demo-stockflow`: the `web` service joins the external `demo-apps` network with the alias `stockflow` (the only thing the proxy talks to), PostgreSQL 16 sits on a private internal network; no published ports, read-only root filesystems, no-new-privileges, dropped capabilities, log rotation, healthchecks, and limits of 0.5 CPU / 768 MB for the whole app. No Redis/Celery worker: tasks run inline and e-mail goes to the console.
- `.env.demo.example` — the secrets to provide (`SECRET_KEY`, `POSTGRES_PASSWORD`, `DEMO_PASSWORD`).

On the server:

```bash
docker network create --internal demo-apps      # once per server (shared with the proxy)
cp .env.demo.example .env.demo                  # fill in fresh random values
chmod 600 .env.demo
docker compose -f compose.demo.yml up -d --build
```

On start the container applies migrations and loads the demo data (`demo_seed`, idempotent). To run it by hand:

```bash
docker compose -f compose.demo.yml exec -T web python manage.py demo_seed
```

Nightly reset (wipes visitor changes and accounts other than superusers, then reloads the demo data) — crontab of the deploy user, adjust the path:

```cron
17 4 * * * cd /srv/demos/stockflow && docker compose -f compose.demo.yml exec -T web python manage.py demo_reset --no-input >> /var/log/demo-stockflow-reset.log 2>&1
```

**Demo login:** user `DEMO_USERNAME` (default `demo`) with the password from `DEMO_PASSWORD` in `.env.demo`. It is a Manager without admin access; `demo_seed` and `demo_reset` set the password again. With `DEMO_SHOW_CREDENTIALS=True` the sign-in page displays it. `demo_seed` and `demo_reset` refuse to run unless `DEMO_MODE=True` (set by `compose.demo.yml`).

## License

MIT — see [LICENSE](LICENSE).
