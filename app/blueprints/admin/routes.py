import os
import re
import uuid
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import bleach
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

from app.extensions import db
from app.models import (
    AdminUser,
    Announcement,
    BlogPost,
    GalleryItem,
    Testimonial,
    SiteStat,
    SiteSetting,
    VideoProfile,
    ManagedPage,
    ContactInfo,
    PPDBProgram,
)

admin_bp = Blueprint("admin", __name__)

ALLOWED_TAGS = [
    "p", "br", "ul", "ol", "li", "strong", "em", "u", "h2", "h3", "h4", "blockquote", "a",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
}


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Masuk")


def _sanitize_html(value):
    cleaned = bleach.clean(
        (value or "").strip(),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return bleach.linkify(cleaned)


def _sanitize_text(value):
    return bleach.clean((value or "").strip(), tags=[], strip=True)


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _extract_iframe_src(value):
    raw = (value or "").strip()
    if not raw:
        return ""
    match = re.search(r'<iframe[^>]*\ssrc=["\']([^"\']+)["\']', raw, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw


def _normalize_youtube_embed_url(value):
    raw = _sanitize_text(_extract_iframe_src(value))
    if not raw:
        return ""
    if "youtube.com/embed/" in raw:
        return raw

    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower()
    path = parsed.path or ""
    if "youtu.be" in host:
        video_id = path.strip("/").split("/")[0]
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
    if "youtube.com" in host:
        if path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"
        if path.startswith("/shorts/"):
            video_id = path.split("/shorts/", 1)[1].split("/")[0]
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"
    return raw


def _normalize_map_embed_url(value):
    raw = _sanitize_text(_extract_iframe_src(value))
    return raw


def _slugify(text):
    text = _sanitize_text(text).lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "artikel"


def _split_teacher_title(raw_title):
    raw = (raw_title or "").strip()
    if "|" in raw:
        left, right = raw.split("|", 1)
        return left.strip(), right.strip()
    if " - " in raw:
        left, right = raw.split(" - ", 1)
        return left.strip(), right.strip()
    return raw, ""


def _compose_media_title(title, category, teacher_subject):
    clean_title = _sanitize_text(title)
    clean_category = _sanitize_text(category)
    clean_subject = _sanitize_text(teacher_subject)
    if clean_category == "Guru":
        if clean_subject:
            return f"{clean_title} | {clean_subject}".strip()
    return clean_title


def _unique_slug(title, current_id=None):
    base = _slugify(title)
    slug = base
    i = 2
    while True:
        q = BlogPost.query.filter_by(slug=slug)
        if current_id is not None:
            q = q.filter(BlogPost.id != current_id)
        if not q.first():
            return slug
        slug = f"{base}-{i}"
        i += 1


def _is_allowed_image(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config.get("MEDIA_ALLOWED_IMAGE_EXTENSIONS", set())


def _save_image_upload(upload, subdir):
    if not upload or not upload.filename:
        return ""

    if not _is_allowed_image(upload.filename):
        raise ValueError("Format gambar tidak didukung. Gunakan PNG/JPG/JPEG/WEBP/GIF.")

    base_folder = current_app.config["MEDIA_UPLOAD_FOLDER"]
    rel_base = current_app.config["MEDIA_UPLOAD_DIR"]
    target_folder = os.path.join(base_folder, subdir)
    os.makedirs(target_folder, exist_ok=True)

    original = secure_filename(upload.filename)
    stem, ext = os.path.splitext(original)
    stem = (stem or "file")[:80]
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    filename = f"{ts}-{suffix}-{stem}{ext.lower()}"
    full_path = os.path.join(target_folder, filename)
    upload.save(full_path)

    return url_for("static", filename=f"{rel_base}/{subdir}/{filename}")


def _get_page(page_key, title):
    page = ManagedPage.query.filter_by(page_key=page_key).first()
    if not page:
        page = ManagedPage(page_key=page_key, title=title)
        db.session.add(page)
    return page


def _get_contact_info():
    info = ContactInfo.query.first()
    if not info:
        info = ContactInfo()
        db.session.add(info)
    return info


def _save_contact_info_from_form(info):
    info.address = _sanitize_html(request.form.get("address"))
    info.email = _sanitize_text(request.form.get("email"))
    info.phone = _sanitize_text(request.form.get("phone"))
    info.whatsapp = _sanitize_text(request.form.get("whatsapp"))
    info.map_embed_url = _normalize_map_embed_url(request.form.get("map_embed_url"))
    info.instagram_url = _sanitize_text(request.form.get("instagram_url"))
    info.facebook_url = _sanitize_text(request.form.get("facebook_url"))
    info.tiktok_url = _sanitize_text(request.form.get("tiktok_url"))
    info.youtube_url = _sanitize_text(request.form.get("youtube_url"))
    db.session.commit()


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("admin.dashboard"))
        flash("Email/password salah.", "danger")
    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@admin_bp.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    info = _get_contact_info()

    if request.method == "POST":
        if request.form.get("form_name") == "contact_info":
            _save_contact_info_from_form(info)
            flash("Contact info berhasil diperbarui.", "success")
            return redirect(url_for("admin.dashboard"))

    data = {
        "announcements": Announcement.query.count(),
        "posts": BlogPost.query.count(),
        "gallery": GalleryItem.query.count(),
        "testimonials": Testimonial.query.count(),
        "hero": GalleryItem.query.filter_by(category="Hero").count(),
        "ppdb_programs": PPDBProgram.query.filter_by(is_active=True).count(),
    }
    return render_template("admin/dashboard.html", data=data, info=info)


@admin_bp.route("/content/beranda", methods=["GET", "POST"])
@login_required
def content_beranda():
    stats = SiteStat.query.first()
    if not stats:
        stats = SiteStat()
        db.session.add(stats)

    video = VideoProfile.query.first()
    if not video:
        video = VideoProfile(title="Video Profil", youtube_embed_url="")
        db.session.add(video)

    if request.method == "POST":
        stats.students_count = _to_int(request.form.get("students_count"), stats.students_count or 0)
        stats.teachers_count = _to_int(request.form.get("teachers_count"), stats.teachers_count or 0)
        stats.alumni_count = _to_int(request.form.get("alumni_count"), stats.alumni_count or 0)
        stats.accreditation = _sanitize_text(request.form.get("accreditation") or "-")

        video.title = _sanitize_text(request.form.get("video_title") or "Video Profil")
        video.youtube_embed_url = _normalize_youtube_embed_url(request.form.get("youtube_embed_url"))

        db.session.commit()
        flash("Konten beranda berhasil disimpan.", "success")
        return redirect(url_for("admin.content_beranda"))

    hero_items = GalleryItem.query.filter_by(category="Hero").order_by(GalleryItem.created_at.desc()).all()
    return render_template("admin/content_beranda.html", stats=stats, video=video, hero_items=hero_items)


@admin_bp.route("/content/profil", methods=["GET", "POST"])
@login_required
def content_profil():
    setting = SiteSetting.query.first()
    if not setting:
        setting = SiteSetting()
        db.session.add(setting)

    if request.method == "POST":
        setting.about_history = _sanitize_html(request.form.get("about_history"))
        setting.about_vision = _sanitize_html(request.form.get("about_vision"))
        setting.about_mission = _sanitize_html(request.form.get("about_mission"))
        setting.headmaster_quote = _sanitize_html(request.form.get("headmaster_quote"))
        setting.headmaster_name = _sanitize_text(request.form.get("headmaster_name"))
        setting.headmaster_photo_url = _sanitize_text(request.form.get("headmaster_photo_url"))

        upload = request.files.get("headmaster_photo")
        if upload and upload.filename:
            try:
                setting.headmaster_photo_url = _save_image_upload(upload, "headmaster")
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("admin.content_profil"))

        db.session.commit()
        flash("Konten profil berhasil disimpan.", "success")
        return redirect(url_for("admin.content_profil"))

    return render_template("admin/content_profil.html", setting=setting)


@admin_bp.route("/content/akademik", methods=["GET", "POST"])
@login_required
def content_akademik():
    return redirect(url_for("admin.content_akademik_sbq"))


@admin_bp.route("/content/akademik/sbq", methods=["GET", "POST"])
@login_required
def content_akademik_sbq():
    page = _get_page("akademik_sbq", "SBQ")
    default_sbq_subtitle = "Program Sekolah Bina Qur'an untuk penguatan adab, ilmu, dan hafalan."
    default_sbq_content = "Konten SBQ dapat Anda kelola dari dashboard admin."
    page_subtitle = (page.subtitle or "").strip()
    page_content = (page.content or "").strip()
    page_is_default = (
        page_subtitle in ("", default_sbq_subtitle)
        and page_content in ("", default_sbq_content)
    )
    if page_is_default:
        legacy_page = ManagedPage.query.filter_by(page_key="akademik").first()
        if legacy_page:
            page.subtitle = legacy_page.subtitle
            page.content = legacy_page.content
            db.session.commit()

    if request.method == "POST":
        page.title = _sanitize_text(request.form.get("title") or "SBQ")
        page.subtitle = _sanitize_html(request.form.get("subtitle"))
        page.content = _sanitize_html(request.form.get("content"))
        db.session.commit()
        flash("Konten SBQ berhasil disimpan.", "success")
        return redirect(url_for("admin.content_akademik_sbq"))

    return render_template(
        "admin/content_akademik_submenu.html",
        page=page,
        page_heading="Kelola Akademik: SBQ",
        submit_label="Simpan Konten SBQ",
    )


@admin_bp.route("/content/akademik/rumah-quran", methods=["GET", "POST"])
@login_required
def content_akademik_rumah_quran():
    page = _get_page("akademik_rumah_quran", "Rumah Qur'an")

    if request.method == "POST":
        page.title = _sanitize_text(request.form.get("title") or "Rumah Qur'an")
        page.subtitle = _sanitize_html(request.form.get("subtitle"))
        page.content = _sanitize_html(request.form.get("content"))
        db.session.commit()
        flash("Konten Rumah Qur'an berhasil disimpan.", "success")
        return redirect(url_for("admin.content_akademik_rumah_quran"))

    return render_template(
        "admin/content_akademik_submenu.html",
        page=page,
        page_heading="Kelola Akademik: Rumah Qur'an",
        submit_label="Simpan Konten Rumah Qur'an",
    )


@admin_bp.route("/content/akademik/takhosus", methods=["GET", "POST"])
@login_required
def content_akademik_takhosus():
    page = _get_page("akademik_takhosus", "Takhosus")

    if request.method == "POST":
        page.title = _sanitize_text(request.form.get("title") or "Takhosus")
        page.subtitle = _sanitize_html(request.form.get("subtitle"))
        page.content = _sanitize_html(request.form.get("content"))
        db.session.commit()
        flash("Konten Takhosus berhasil disimpan.", "success")
        return redirect(url_for("admin.content_akademik_takhosus"))

    return render_template(
        "admin/content_akademik_submenu.html",
        page=page,
        page_heading="Kelola Akademik: Takhosus",
        submit_label="Simpan Konten Takhosus",
    )


@admin_bp.route("/content/akademik/majelis-talim", methods=["GET", "POST"])
@login_required
def content_akademik_majelis_talim():
    page = _get_page("akademik_majelis_talim", "Majelis Ta'lim")

    if request.method == "POST":
        page.title = _sanitize_text(request.form.get("title") or "Majelis Ta'lim")
        page.subtitle = _sanitize_html(request.form.get("subtitle"))
        page.content = _sanitize_html(request.form.get("content"))
        db.session.commit()
        flash("Konten Majelis Ta'lim berhasil disimpan.", "success")
        return redirect(url_for("admin.content_akademik_majelis_talim"))

    return render_template(
        "admin/content_akademik_submenu.html",
        page=page,
        page_heading="Kelola Akademik: Majelis Ta'lim",
        submit_label="Simpan Konten Majelis Ta'lim",
    )


@admin_bp.route("/content/kesiswaan", methods=["GET", "POST"])
@login_required
def content_kesiswaan():
    return redirect(url_for("admin.content_kesiswaan_daily_activity"))


@admin_bp.route("/content/kesiswaan/daily-activity", methods=["GET", "POST"])
@login_required
def content_kesiswaan_daily_activity():
    page = _get_page("kesiswaan_daily_activity", "Daily Activity")

    if request.method == "POST":
        page.title = _sanitize_text(request.form.get("title") or "Daily Activity")
        page.subtitle = _sanitize_html(request.form.get("subtitle"))
        page.content = _sanitize_html(request.form.get("content"))
        db.session.commit()
        flash("Konten Daily Activity berhasil disimpan.", "success")
        return redirect(url_for("admin.content_kesiswaan_daily_activity"))

    return render_template(
        "admin/content_kesiswaan_submenu.html",
        page=page,
        page_heading="Kelola Kesiswaan: Daily Activity",
        submit_label="Simpan Konten Daily Activity",
    )


@admin_bp.route("/content/kesiswaan/ekstrakulikuler", methods=["GET", "POST"])
@login_required
def content_kesiswaan_ekstrakulikuler():
    page = _get_page("kesiswaan_ekstrakulikuler", "Ekstrakulikuler")

    if request.method == "POST":
        page.title = _sanitize_text(request.form.get("title") or "Ekstrakulikuler")
        page.subtitle = _sanitize_html(request.form.get("subtitle"))
        page.content = _sanitize_html(request.form.get("content"))
        db.session.commit()
        flash("Konten Ekstrakulikuler berhasil disimpan.", "success")
        return redirect(url_for("admin.content_kesiswaan_ekstrakulikuler"))

    return render_template(
        "admin/content_kesiswaan_submenu.html",
        page=page,
        page_heading="Kelola Kesiswaan: Ekstrakulikuler",
        submit_label="Simpan Konten Ekstrakulikuler",
    )


@admin_bp.route("/content/kesiswaan/organisasi-santri", methods=["GET", "POST"])
@login_required
def content_kesiswaan_organisasi_santri():
    page = _get_page("kesiswaan_organisasi_santri", "Organisasi Santri")

    if request.method == "POST":
        page.title = _sanitize_text(request.form.get("title") or "Organisasi Santri")
        page.subtitle = _sanitize_html(request.form.get("subtitle"))
        page.content = _sanitize_html(request.form.get("content"))
        db.session.commit()
        flash("Konten Organisasi Santri berhasil disimpan.", "success")
        return redirect(url_for("admin.content_kesiswaan_organisasi_santri"))

    return render_template(
        "admin/content_kesiswaan_submenu.html",
        page=page,
        page_heading="Kelola Kesiswaan: Organisasi Santri",
        submit_label="Simpan Konten Organisasi Santri",
    )


@admin_bp.route("/content/kontak", methods=["GET", "POST"])
@login_required
def content_kontak():
    info = _get_contact_info()

    if request.method == "POST":
        _save_contact_info_from_form(info)
        flash("Konten kontak berhasil disimpan.", "success")
        return redirect(url_for("admin.content_kontak"))

    return render_template("admin/content_kontak.html", info=info)


@admin_bp.route("/content/berita", methods=["GET", "POST"])
@login_required
def content_berita():
    if request.method == "POST":
        title = _sanitize_text(request.form.get("title"))
        excerpt = _sanitize_text(request.form.get("excerpt"))
        body = _sanitize_html(request.form.get("body"))
        manual_slug = _sanitize_text(request.form.get("slug"))
        is_published = request.form.get("is_published") == "on"

        if not title:
            flash("Judul artikel wajib diisi.", "danger")
            return redirect(url_for("admin.content_berita"))

        cover_url = _sanitize_text(request.form.get("cover_url"))
        upload = request.files.get("cover_photo")
        if upload and upload.filename:
            try:
                cover_url = _save_image_upload(upload, "blog")
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("admin.content_berita"))

        if request.form.get("action") == "preview":
            fake = {
                "title": title,
                "excerpt": excerpt,
                "body": body,
                "cover_url": cover_url,
                "is_published": is_published,
                "slug": manual_slug or _slugify(title),
                "published_at": datetime.utcnow(),
            }
            return render_template("admin/preview_post.html", post=fake)

        post = BlogPost(
            title=title,
            slug=_unique_slug(manual_slug or title),
            excerpt=excerpt,
            body=body,
            cover_url=cover_url,
            is_published=is_published,
            published_at=datetime.utcnow(),
        )
        db.session.add(post)
        db.session.commit()
        flash("Artikel berhasil disimpan.", "success")
        return redirect(url_for("admin.content_berita"))

    posts = BlogPost.query.order_by(BlogPost.published_at.desc()).all()
    return render_template("admin/content_berita.html", posts=posts)


@admin_bp.route("/content/berita/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_berita(post_id):
    post = BlogPost.query.get_or_404(post_id)

    if request.method == "POST":
        post.title = _sanitize_text(request.form.get("title") or post.title)
        post.excerpt = _sanitize_text(request.form.get("excerpt"))
        post.body = _sanitize_html(request.form.get("body"))
        post.is_published = request.form.get("is_published") == "on"

        manual_slug = _sanitize_text(request.form.get("slug"))
        post.slug = _unique_slug(manual_slug or post.title, current_id=post.id)

        cover_url = _sanitize_text(request.form.get("cover_url"))
        if cover_url:
            post.cover_url = cover_url

        upload = request.files.get("cover_photo")
        if upload and upload.filename:
            try:
                post.cover_url = _save_image_upload(upload, "blog")
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("admin.edit_berita", post_id=post.id))

        if request.form.get("action") == "preview":
            fake = {
                "title": post.title,
                "excerpt": post.excerpt,
                "body": post.body,
                "cover_url": post.cover_url,
                "is_published": post.is_published,
                "slug": post.slug,
                "published_at": post.published_at,
            }
            return render_template("admin/preview_post.html", post=fake)

        db.session.commit()
        flash("Artikel berhasil diperbarui.", "success")
        return redirect(url_for("admin.content_berita"))

    return render_template("admin/edit_berita.html", post=post)


@admin_bp.route("/content/berita/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_berita(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Artikel dihapus.", "success")
    return redirect(url_for("admin.content_berita"))


@admin_bp.route("/content/pengumuman", methods=["GET", "POST"])
@login_required
def content_pengumuman():
    if request.method == "POST":
        title = _sanitize_text(request.form.get("title"))
        summary = _sanitize_text(request.form.get("summary"))
        body = _sanitize_html(request.form.get("body"))
        is_published = request.form.get("is_published") == "on"

        if not title:
            flash("Judul pengumuman wajib diisi.", "danger")
            return redirect(url_for("admin.content_pengumuman"))

        if request.form.get("action") == "preview":
            fake = {
                "title": title,
                "summary": summary,
                "body": body,
                "is_published": is_published,
                "published_at": datetime.utcnow(),
            }
            return render_template("admin/preview_announcement.html", item=fake)

        item = Announcement(
            title=title,
            summary=summary,
            body=body,
            is_published=is_published,
            published_at=datetime.utcnow(),
        )
        db.session.add(item)
        db.session.commit()
        flash("Pengumuman berhasil disimpan.", "success")
        return redirect(url_for("admin.content_pengumuman"))

    items = Announcement.query.order_by(Announcement.published_at.desc()).all()
    return render_template("admin/content_pengumuman.html", items=items)


@admin_bp.route("/content/pengumuman/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_pengumuman(item_id):
    item = Announcement.query.get_or_404(item_id)

    if request.method == "POST":
        item.title = _sanitize_text(request.form.get("title") or item.title)
        item.summary = _sanitize_text(request.form.get("summary"))
        item.body = _sanitize_html(request.form.get("body"))
        item.is_published = request.form.get("is_published") == "on"

        if request.form.get("action") == "preview":
            fake = {
                "title": item.title,
                "summary": item.summary,
                "body": item.body,
                "is_published": item.is_published,
                "published_at": item.published_at,
            }
            return render_template("admin/preview_announcement.html", item=fake)

        db.session.commit()
        flash("Pengumuman berhasil diperbarui.", "success")
        return redirect(url_for("admin.content_pengumuman"))

    return render_template("admin/edit_pengumuman.html", item=item)


@admin_bp.route("/content/pengumuman/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_pengumuman(item_id):
    item = Announcement.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Pengumuman dihapus.", "success")
    return redirect(url_for("admin.content_pengumuman"))


@admin_bp.route("/content/media", methods=["GET", "POST"])
@login_required
def content_media():
    if request.method == "POST":
        title = request.form.get("title")
        category = _sanitize_text(request.form.get("category") or "Kegiatan")
        teacher_subject = request.form.get("teacher_subject")
        title = _compose_media_title(title, category, teacher_subject)
        image_url = _sanitize_text(request.form.get("image_url"))

        upload = request.files.get("gallery_photo")
        if upload and upload.filename:
            try:
                image_url = _save_image_upload(upload, "gallery")
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("admin.content_media"))

        if not image_url:
            flash("Masukkan URL gambar atau upload foto.", "danger")
            return redirect(url_for("admin.content_media"))

        item = GalleryItem(title=title, category=category, image_url=image_url)
        db.session.add(item)
        db.session.commit()
        flash("Media berhasil ditambahkan.", "success")
        return redirect(url_for("admin.content_media"))

    items = GalleryItem.query.order_by(GalleryItem.created_at.desc()).all()
    return render_template("admin/content_media.html", items=items)


@admin_bp.route("/content/media/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_media(item_id):
    item = GalleryItem.query.get_or_404(item_id)
    teacher_name, teacher_subject = _split_teacher_title(item.title)

    if request.method == "POST":
        form_category = _sanitize_text(request.form.get("category") or item.category)
        item.title = _compose_media_title(
            request.form.get("title"),
            form_category,
            request.form.get("teacher_subject"),
        )
        item.category = form_category
        image_url = _sanitize_text(request.form.get("image_url"))
        if image_url:
            item.image_url = image_url

        upload = request.files.get("gallery_photo")
        if upload and upload.filename:
            try:
                item.image_url = _save_image_upload(upload, "gallery")
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("admin.edit_media", item_id=item.id))

        db.session.commit()
        flash("Media berhasil diperbarui.", "success")
        return redirect(url_for("admin.content_media"))

    return render_template(
        "admin/edit_media.html",
        item=item,
        teacher_name=teacher_name,
        teacher_subject=teacher_subject,
    )


@admin_bp.route("/content/media/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_media(item_id):
    item = GalleryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Media dihapus.", "success")
    return redirect(url_for("admin.content_media"))


@admin_bp.route("/content/testimoni", methods=["GET", "POST"])
@login_required
def content_testimoni():
    if request.method == "POST":
        name = _sanitize_text(request.form.get("name"))
        quote = _sanitize_text(request.form.get("quote"))
        if not name or not quote:
            flash("Nama dan isi testimoni wajib diisi.", "danger")
            return redirect(url_for("admin.content_testimoni"))

        photo_url = _sanitize_text(request.form.get("photo_url"))
        upload = request.files.get("testimonial_photo")
        if upload and upload.filename:
            try:
                photo_url = _save_image_upload(upload, "testimonials")
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("admin.content_testimoni"))

        item = Testimonial(
            name=name,
            role=_sanitize_text(request.form.get("role") or "Orang Tua"),
            quote=quote,
            photo_url=photo_url,
        )
        db.session.add(item)
        db.session.commit()
        flash("Testimoni berhasil disimpan.", "success")
        return redirect(url_for("admin.content_testimoni"))

    items = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template("admin/content_testimoni.html", items=items)


@admin_bp.route("/content/testimoni/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_testimoni(item_id):
    item = Testimonial.query.get_or_404(item_id)

    if request.method == "POST":
        item.name = _sanitize_text(request.form.get("name") or item.name)
        item.role = _sanitize_text(request.form.get("role") or item.role)
        item.quote = _sanitize_text(request.form.get("quote") or item.quote)
        photo_url = _sanitize_text(request.form.get("photo_url"))
        if photo_url:
            item.photo_url = photo_url

        upload = request.files.get("testimonial_photo")
        if upload and upload.filename:
            try:
                item.photo_url = _save_image_upload(upload, "testimonials")
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("admin.edit_testimoni", item_id=item.id))

        db.session.commit()
        flash("Testimoni berhasil diperbarui.", "success")
        return redirect(url_for("admin.content_testimoni"))

    return render_template("admin/edit_testimoni.html", item=item)


@admin_bp.route("/content/testimoni/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_testimoni(item_id):
    item = Testimonial.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Testimoni dihapus.", "success")
    return redirect(url_for("admin.content_testimoni"))


@admin_bp.route("/content/ppdb", methods=["GET", "POST"])
@login_required
def content_ppdb():
    if request.method == "POST":
        name = _sanitize_text(request.form.get("name"))
        if not name:
            flash("Nama program PPDB wajib diisi.", "danger")
            return redirect(url_for("admin.content_ppdb"))

        program = PPDBProgram(
            name=name,
            levels=_sanitize_text(request.form.get("levels")),
            description=_sanitize_html(request.form.get("description")),
            external_url=_sanitize_text(request.form.get("external_url") or current_app.config.get("PPDB_SYSTEM_URL") or ""),
            sort_order=_to_int(request.form.get("sort_order"), 0),
            is_active=(request.form.get("is_active") == "on"),
        )
        db.session.add(program)
        db.session.commit()
        flash("Program PPDB berhasil ditambahkan.", "success")
        return redirect(url_for("admin.content_ppdb"))

    programs = PPDBProgram.query.order_by(PPDBProgram.sort_order.asc(), PPDBProgram.id.asc()).all()
    return render_template("admin/content_ppdb.html", programs=programs)


@admin_bp.route("/content/ppdb/<int:program_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ppdb(program_id):
    program = PPDBProgram.query.get_or_404(program_id)

    if request.method == "POST":
        program.name = _sanitize_text(request.form.get("name") or program.name)
        program.levels = _sanitize_text(request.form.get("levels"))
        program.description = _sanitize_html(request.form.get("description"))
        program.external_url = _sanitize_text(request.form.get("external_url") or program.external_url)
        program.sort_order = _to_int(request.form.get("sort_order"), program.sort_order)
        program.is_active = request.form.get("is_active") == "on"
        db.session.commit()
        flash("Program PPDB berhasil diperbarui.", "success")
        return redirect(url_for("admin.content_ppdb"))

    return render_template("admin/edit_ppdb.html", program=program)


@admin_bp.route("/content/ppdb/<int:program_id>/delete", methods=["POST"])
@login_required
def delete_ppdb(program_id):
    program = PPDBProgram.query.get_or_404(program_id)
    db.session.delete(program)
    db.session.commit()
    flash("Program PPDB dihapus.", "success")
    return redirect(url_for("admin.content_ppdb"))
