# StockFlow

![CI](https://github.com/msaeiid/stockflow/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> A small-business inventory and order management system — track stock, prevent over-selling, and get low-stock alerts.

StockFlow is a full-stack web application that helps small businesses manage products, warehouses, suppliers, and customer orders. It automatically updates stock levels as orders are placed, blocks orders that exceed available inventory, and notifies managers when an item runs low.

## 🔗 Live demo

**App:** ⟨https://stockflow-eight-sigma.vercel.app⟩
**API docs:** ⟨https://stockflow-api-ujk2.onrender.com/api/docs/⟩

**Demo login:** `demo` / `demo12345`

> ⏳ The backend runs on a free tier and may take ~30 seconds to wake up on the first request.

![Dashboard](docs/dashboard.png)

## Features

- 📊 Reporting dashboard with key metrics and stock-level charts
- 📦 Product, warehouse, supplier & customer management
- 🛒 Customer orders with **atomic** multi-item stock deduction
- 🛡️ Validation that prevents over-selling (no negative stock)
- 🔔 Low-stock alerts via background jobs (Celery)
- 🔐 JWT auth with role-based access (admin / manager / staff)
- 📄 REST API documented with Swagger & ReDoc

## Tech stack

**Backend:** Python, Django, Django REST Framework, PostgreSQL, Celery, Redis
**Frontend:** React, TypeScript, Vite, React Router, Recharts
**Infrastructure:** Docker, Docker Compose, GitHub Actions (CI)
**Testing:** pytest · **Linting:** Ruff

## Architecture



React + TypeScript (Vite)          ← deployed on Vercel
│  REST / JSON + JWT
▼
Django REST Framework + Celery      ← deployed on Render
│  ORM
▼
PostgreSQL          Redis (broker / cache)


## Key engineering decisions

- **Atomic stock deduction** — orders deduct stock for all items inside a single database transaction; if any item is short, the whole order rolls back (no partial orders, no negative stock).
- **Concurrency-safe** — stock updates use `select_for_update()` to prevent race conditions under simultaneous requests.
- **Async by design** — low-stock alerts run as background Celery tasks, dispatched via `transaction.on_commit` so they never fire before data is committed.
- **Graceful degradation** — Redis is optional; without it, the app falls back to an in-memory cache and runs tasks inline, so it deploys anywhere.
- **Price snapshots** — order items store the unit price at time of sale, independent of later product price changes.

## Getting started

### Prerequisites
- Docker & Docker Compose

### Run locally
```bash
git clone https://github.com/msaeiid/stockflow.git
cd stockflow
cp backend/.env.example backend/.env
docker compose up --build
```
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/api/docs/`

### Frontend (dev)
```bash
cd frontend
npm install
npm run dev
```
App runs at `http://localhost:5173`.

### Seed sample data
```bash
docker compose exec web python manage.py seed_data
```

## Running tests
```bash
docker compose exec web pytest -v
```

## License
MIT — see [LICENSE](LICENSE).
