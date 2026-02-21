import os
from flask import Flask
from sqlalchemy import text
from .config import Config
from .extensions import db, migrate, login_manager
from .models import AdminUser, SiteSetting, SiteStat, VideoProfile, ManagedPage, ContactInfo, PPDBProgram

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.validate()
    media_rel = (app.config.get("MEDIA_UPLOAD_DIR") or "uploads/media").strip("/\\")
    app.config["MEDIA_UPLOAD_DIR"] = media_rel
    app.config["MEDIA_UPLOAD_FOLDER"] = os.path.join(app.static_folder, media_rel)
    os.makedirs(app.config["MEDIA_UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .blueprints.main.routes import main_bp
    from .blueprints.profile.routes import profile_bp
    from .blueprints.academic.routes import academic_bp
    from .blueprints.studentlife.routes import studentlife_bp
    from .blueprints.ppdb.routes import ppdb_bp
    from .blueprints.blog.routes import blog_bp
    from .blueprints.contact.routes import contact_bp
    from .blueprints.admin.routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(profile_bp, url_prefix="/profil")
    app.register_blueprint(academic_bp, url_prefix="/akademik")
    app.register_blueprint(studentlife_bp, url_prefix="/kesiswaan")
    app.register_blueprint(ppdb_bp, url_prefix="/ppdb")
    app.register_blueprint(blog_bp, url_prefix="/berita")
    app.register_blueprint(contact_bp, url_prefix="/kontak")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    @app.context_processor
    def inject_globals():
        contact_info = ContactInfo.query.first()
        return dict(
            SCHOOL_SYSTEM_URL=app.config.get("SCHOOL_SYSTEM_URL"),
            PPDB_SYSTEM_URL=app.config.get("PPDB_SYSTEM_URL"),
            SCHOOL_NAME=app.config.get("SCHOOL_NAME"),
            SCHOOL_PHONE=app.config.get("SCHOOL_PHONE"),
            SCHOOL_WHATSAPP=app.config.get("SCHOOL_WHATSAPP"),
            SCHOOL_EMAIL=app.config.get("SCHOOL_EMAIL"),
            SCHOOL_ADDRESS=app.config.get("SCHOOL_ADDRESS"),
            SCHOOL_MAP_EMBED_URL=app.config.get("SCHOOL_MAP_EMBED_URL"),
            CONTACT_INFO=contact_info,
        )

    with app.app_context():
        try:
            bootstrap_required = (
                app.config.get("DB_CREATE_ALL_ON_STARTUP")
                or app.config.get("SEED_ON_STARTUP")
            )
            if bootstrap_required:
                # Early connectivity check so auth/connection issues are logged clearly.
                db.session.execute(text("SELECT 1"))

            if app.config.get("DB_CREATE_ALL_ON_STARTUP"):
                # Keep disabled in production and run migrations explicitly instead.
                db.create_all()

            if not app.config.get("SEED_ON_STARTUP"):
                return app

            # Seed minimal rows if empty (independen per tabel)
            if not SiteSetting.query.first():
                db.session.add(SiteSetting(
                    about_history="(Isi sejarah & identitas di admin nanti)",
                    about_vision="(Isi visi)",
                    about_mission="(Isi misi)",
                    headmaster_quote="(Kutipan 1–2 paragraf kepala sekolah/pengasuh)",
                    headmaster_name="(Nama Kepala Sekolah)",
                    headmaster_photo_url=""
                ))

            if not SiteStat.query.first():
                db.session.add(SiteStat(
                    students_count=0,
                    teachers_count=0,
                    alumni_count=0,
                    accreditation="-"
                ))

            if not VideoProfile.query.first():
                db.session.add(VideoProfile(
                    title="Video Profil",
                    youtube_embed_url="https://www.youtube.com/embed/dQw4w9WgXcQ"
                ))

            if not ManagedPage.query.filter_by(page_key="akademik_sbq").first():
                db.session.add(ManagedPage(
                    page_key="akademik_sbq",
                    title="SBQ",
                    subtitle="Program Sekolah Bina Qur'an untuk penguatan adab, ilmu, dan hafalan.",
                    content="Konten SBQ dapat Anda kelola dari dashboard admin.",
                    points=""
                ))

            if not ManagedPage.query.filter_by(page_key="akademik_rumah_quran").first():
                db.session.add(ManagedPage(
                    page_key="akademik_rumah_quran",
                    title="Rumah Qur'an",
                    subtitle="Program pembelajaran Al-Qur'an berbasis halaqah dan pendampingan bertahap.",
                    content="Konten Rumah Qur'an dapat Anda kelola dari dashboard admin.",
                    points=""
                ))

            if not ManagedPage.query.filter_by(page_key="akademik_takhosus").first():
                db.session.add(ManagedPage(
                    page_key="akademik_takhosus",
                    title="Takhosus",
                    subtitle="Program takhosus untuk pendalaman materi tertentu secara intensif.",
                    content="Konten Takhosus dapat Anda kelola dari dashboard admin.",
                    points=""
                ))

            if not ManagedPage.query.filter_by(page_key="akademik_majelis_talim").first():
                db.session.add(ManagedPage(
                    page_key="akademik_majelis_talim",
                    title="Majelis Ta'lim",
                    subtitle="Program kajian rutin untuk pembinaan ilmu dan karakter peserta didik.",
                    content="Konten Majelis Ta'lim dapat Anda kelola dari dashboard admin.",
                    points=""
                ))

            # Recovery: migrate legacy "akademik" content to SBQ when SBQ still uses default seed content.
            legacy_akademik = ManagedPage.query.filter_by(page_key="akademik").first()
            sbq_page = ManagedPage.query.filter_by(page_key="akademik_sbq").first()
            if legacy_akademik and sbq_page:
                default_sbq_subtitle = "Program Sekolah Bina Qur'an untuk penguatan adab, ilmu, dan hafalan."
                default_sbq_content = "Konten SBQ dapat Anda kelola dari dashboard admin."
                sbq_subtitle = (sbq_page.subtitle or "").strip()
                sbq_content = (sbq_page.content or "").strip()
                sbq_is_default = (
                    sbq_subtitle in ("", default_sbq_subtitle)
                    and sbq_content in ("", default_sbq_content)
                )
                if sbq_is_default:
                    sbq_page.subtitle = legacy_akademik.subtitle
                    sbq_page.content = legacy_akademik.content

            if not ManagedPage.query.filter_by(page_key="kesiswaan").first():
                db.session.add(ManagedPage(
                    page_key="kesiswaan",
                    title="Kesiswaan",
                    subtitle="Informasi kegiatan siswa, organisasi, pembinaan karakter, dan agenda kesiswaan.",
                    content="Halaman kesiswaan dapat Anda kelola dari dashboard admin.",
                    points="Organisasi Siswa\nEkstrakurikuler\nPembinaan Karakter"
                ))

            if not ManagedPage.query.filter_by(page_key="kesiswaan_daily_activity").first():
                db.session.add(ManagedPage(
                    page_key="kesiswaan_daily_activity",
                    title="Daily Activity",
                    subtitle="Kegiatan harian santri untuk membangun disiplin, adab, dan kemandirian.",
                    content="Konten daily activity dapat Anda kelola dari database managed_pages (page_key: kesiswaan_daily_activity).",
                    points="Sholat berjamaah\nBelajar kelas\nMurojaah dan halaqah"
                ))

            if not ManagedPage.query.filter_by(page_key="kesiswaan_ekstrakulikuler").first():
                db.session.add(ManagedPage(
                    page_key="kesiswaan_ekstrakulikuler",
                    title="Ekstrakulikuler",
                    subtitle="Pilihan kegiatan minat dan bakat santri di luar kegiatan akademik utama.",
                    content="Konten ekstrakulikuler dapat Anda kelola dari database managed_pages (page_key: kesiswaan_ekstrakulikuler).",
                    points="Olahraga\nPramuka\nSeni dan kreativitas"
                ))

            if not ManagedPage.query.filter_by(page_key="kesiswaan_organisasi_santri").first():
                db.session.add(ManagedPage(
                    page_key="kesiswaan_organisasi_santri",
                    title="Organisasi Santri",
                    subtitle="Wadah kepemimpinan santri untuk belajar tanggung jawab, kolaborasi, dan pelayanan.",
                    content="Konten organisasi santri dapat Anda kelola dari database managed_pages (page_key: kesiswaan_organisasi_santri).",
                    points="Program kerja santri\nPelatihan kepemimpinan\nKoordinasi kegiatan asrama"
                ))

            if not ContactInfo.query.first():
                db.session.add(ContactInfo(
                    address=app.config.get("SCHOOL_ADDRESS") or "",
                    email=app.config.get("SCHOOL_EMAIL") or "",
                    phone=app.config.get("SCHOOL_PHONE") or "",
                    whatsapp=app.config.get("SCHOOL_WHATSAPP") or "",
                    map_embed_url=app.config.get("SCHOOL_MAP_EMBED_URL") or "",
                ))

            if not PPDBProgram.query.first():
                base_url = app.config.get("PPDB_SYSTEM_URL") or "https://ppdb.rqdf.co.id"
                programs = [
                    ("Sekolah Bina Qur'an", "SD, SMP, SMA", "Program pendidikan formal terpadu berbasis nilai Al-Qur'an."),
                    ("Program Tahfidz Reguler", "SMP, SMA", "Program tahfidz dengan kurikulum reguler untuk target hafalan bertahap."),
                    ("Takhosus Tahfidz", "SMP, SMA", "Program intensif tahfidz untuk fokus capaian hafalan dan mutqin."),
                    ("Sekolah Ummahat", "Dewasa", "Program pembinaan keilmuan dan keislaman khusus muslimah/ummahat."),
                ]
                for idx, (name, levels, desc) in enumerate(programs, start=1):
                    db.session.add(PPDBProgram(
                        name=name,
                        levels=levels,
                        description=desc,
                        external_url=base_url,
                        sort_order=idx,
                        is_active=True,
                    ))

            # Seed admin kalau kredensial tersedia
            admin_email = app.config.get("ADMIN_EMAIL")
            admin_password = app.config.get("ADMIN_PASSWORD")
            if admin_email and admin_password:
                admin = AdminUser.query.filter_by(email=admin_email).first()
                if not admin:
                    admin = AdminUser(email=admin_email)
                    admin.set_password(admin_password)
                    db.session.add(admin)

            db.session.commit()

        except UnicodeDecodeError as e:
            db.session.rollback()
            app.logger.error(
                "Koneksi DB gagal (UnicodeDecodeError). "
                "Periksa DATABASE_URL (terutama user/password) dan encoding PostgreSQL. Detail: %s",
                e,
            )
            if app.config.get("FAIL_FAST_ON_DB_ERROR"):
                raise
        except Exception as e:
            db.session.rollback()
            app.logger.exception("Seeding gagal: %s", e)
            if app.config.get("FAIL_FAST_ON_DB_ERROR"):
                raise

    return app
