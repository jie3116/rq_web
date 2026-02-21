# Website RQDF

Website sekolah berbasis Flask dengan PostgreSQL, siap untuk:
- development lokal (Python host + DB Docker)
- deployment production (Docker Compose + Nginx + Gunicorn)

## Tech Stack
- Python 3.10
- Flask
- SQLAlchemy + Flask-Migrate
- PostgreSQL 15
- Gunicorn
- Nginx (reverse proxy + TLS)
- Docker Compose

## Struktur File Penting
- `app/` source code aplikasi
- `manage.py` entrypoint development
- `run.py` entrypoint WSGI untuk Gunicorn
- `Dockerfile` image aplikasi
- `docker-compose.yml` stack dasar (`web` + `db`)
- `docker-compose.prod.yml` override production (termasuk `nginx`)
- `nginx/rqdf.co.id.conf` konfigurasi domain
- `.env.local.example` template env lokal
- `.env.production.example` template env production
- `DEPLOYMENT.md` panduan deploy ringkas

## Prasyarat
- Docker + Docker Compose
- Python 3.10+ (jika ingin run host lokal tanpa container app)

## Setup Lokal (Recommended untuk Development)
1. Buat file env:
   - copy `.env.local.example` menjadi `.env`
2. Jalankan database:
   - `docker compose up -d db`
3. Install dependency Python:
   - `pip install -r requirements.txt`
4. Jalankan aplikasi:
   - `python manage.py`
5. Akses:
   - `http://127.0.0.1:5000`

Catatan:
- mode lokal default mengaktifkan bootstrap DB awal (`DB_CREATE_ALL_ON_STARTUP=true`, `SEED_ON_STARTUP=true`)

## Menjalankan Full Stack Production
1. Di server, copy `.env.production.example` menjadi `.env`
2. Isi semua secret dengan nilai aman:
   - `SECRET_KEY`
   - `POSTGRES_PASSWORD`
   - `ADMIN_PASSWORD`
3. Pastikan sertifikat TLS tersedia:
   - `/etc/letsencrypt/live/rqdf.co.id/fullchain.pem`
   - `/etc/letsencrypt/live/rqdf.co.id/privkey.pem`
4. Jalankan stack:
   - `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`

## Operasional
- Lihat status:
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml ps`
- Lihat log:
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f web`
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f nginx`
- Stop stack:
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml down`

## Keamanan
- Jangan commit `.env` ke repository
- Gunakan secret kuat di production
- Pastikan `FLASK_DEBUG=false` di production
- Di production, bootstrap otomatis DB dimatikan:
  - `DB_CREATE_ALL_ON_STARTUP=false`
  - `SEED_ON_STARTUP=false`
- Jalankan migrasi database secara eksplisit saat rilis

## Domain Production
- Primary domain: `rqdf.co.id`
- `www.rqdf.co.id` diarahkan ke domain utama

## Lisensi
Internal project RQDF.
