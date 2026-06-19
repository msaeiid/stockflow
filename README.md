# StockFlow

![CI](https://github.com/msaeiid/stockflow/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> A small-business inventory and order management system — track stock, prevent over-selling, and get low-stock alerts.

StockFlow is a full-stack web application that helps small businesses manage
products, warehouses, suppliers, and customer orders. It automatically updates
stock levels as orders are placed, blocks orders that exceed available
inventory, and notifies managers when an item runs low.

**Status:** 🚧 In active development

## Features

- [ ] Product, warehouse, supplier & customer management
- [ ] Customer orders with automatic stock deduction
- [ ] Validation to prevent over-selling (no negative stock)
- [ ] Low-stock threshold alerts (email via background jobs)
- [ ] Role-based access (admin / manager / staff)
- [ ] Reporting dashboard with charts
- [ ] REST API documented with Swagger

## API Documentation
Interactive API docs available at `/api/docs/` (Swagger) and `/api/redoc/` (ReDoc).

## Tech Stack

**Backend:** Python, Django, Django REST Framework, PostgreSQL, Celery, Redis
**Frontend:** React, TypeScript, Vite
**Infrastructure:** Docker, GitHub Actions (CI/CD)
**Testing:** pytest

## Getting Started

_Setup instructions will be added as the project develops._

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.
