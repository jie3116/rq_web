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
3. Pastikan media upload dipersist di server:
   - folder yang dipakai app: `/app/app/static/uploads/media`
   - di stack ini folder tersebut di-mount ke named volume `media_uploads`
   - file lama dari laptop/local tidak otomatis ikut saat fresh deploy jika tidak pernah disalin ke volume server
4. Start stack:
   - `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`

`web` in production is forced to:
- `FLASK_ENV=production`
- `FLASK_DEBUG=false`
- `DATABASE_URL` with host `db`
- no auto `db.create_all()` and no auto seeding

## 2.1) Restore/Sync Media Lama ke Server (Penting)
Jika setelah deploy gambar lama (kepala sekolah/hero/guru) hilang, biasanya DB masih menyimpan URL
`/static/uploads/media/...` tetapi file fisiknya belum ada di volume server.

Contoh sync dari folder lokal ke volume server:
- jalankan stack production dulu (`web` aktif)
- copy file media ke container `web`:
  - `docker cp ./app/static/uploads/media/. sekolah_app:/app/app/static/uploads/media/`

Cek isi media di container:
- `docker exec -it sekolah_app ls -lah /app/app/static/uploads/media`

## 3) Security Checklist
- Never commit real `.env` into git.
- Use strong `SECRET_KEY` in production.
- Rotate `POSTGRES_PASSWORD` and `ADMIN_PASSWORD` before go-live.
- Keep `TRUSTED_HOSTS` aligned with production domains.
