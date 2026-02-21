# Deployment Guide

## 1) Local Development (host Python + Docker Postgres)
1. Copy `.env.local.example` to `.env` and fill values.
2. Start database only:
   - `docker compose up -d db`
3. Run app from host:
   - `python manage.py`

App will use `DATABASE_URL` from `.env` (localhost).

## 2) Production (Docker stack)
1. Copy `.env.production.example` to `.env` on server and fill secure values.
2. Make sure SSL cert exists:
   - `/etc/letsencrypt/live/rqdf.co.id/fullchain.pem`
   - `/etc/letsencrypt/live/rqdf.co.id/privkey.pem`
3. Start stack:
   - `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`

`web` in production is forced to:
- `FLASK_ENV=production`
- `FLASK_DEBUG=false`
- `DATABASE_URL` with host `db`
- no auto `db.create_all()` and no auto seeding

## 3) Security Checklist
- Never commit real `.env` into git.
- Use strong `SECRET_KEY` in production.
- Rotate `POSTGRES_PASSWORD` and `ADMIN_PASSWORD` before go-live.
- Keep `TRUSTED_HOSTS` aligned with production domains.
