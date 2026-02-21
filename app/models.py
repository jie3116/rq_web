from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db

class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw: str):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

class SiteSetting(db.Model):
    __tablename__ = "site_settings"
    id = db.Column(db.Integer, primary_key=True)
    about_history = db.Column(db.Text, default="")
    about_vision = db.Column(db.Text, default="")
    about_mission = db.Column(db.Text, default="")
    headmaster_quote = db.Column(db.Text, default="")
    headmaster_name = db.Column(db.String(120), default="")
    headmaster_photo_url = db.Column(db.String(255), default="")

class Announcement(db.Model):
    __tablename__ = "announcements"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(300), default="")
    body = db.Column(db.Text, default="")
    is_published = db.Column(db.Boolean, default=True)
    published_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(220), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    excerpt = db.Column(db.String(300), default="")
    body = db.Column(db.Text, default="")
    cover_url = db.Column(db.String(255), default="")
    is_published = db.Column(db.Boolean, default=True)
    published_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class GalleryItem(db.Model):
    __tablename__ = "gallery_items"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), default="")
    image_url = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(80), default="Fasilitas")  # Fasilitas / Kegiatan / dll
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Testimonial(db.Model):
    __tablename__ = "testimonials"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), default="Orang Tua")
    quote = db.Column(db.String(400), nullable=False)
    photo_url = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VideoProfile(db.Model):
    __tablename__ = "video_profiles"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), default="Video Profil")
    youtube_embed_url = db.Column(db.String(255), nullable=False)  # link embed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SiteStat(db.Model):
    __tablename__ = "site_stats"
    id = db.Column(db.Integer, primary_key=True)
    students_count = db.Column(db.Integer, default=0)
    teachers_count = db.Column(db.Integer, default=0)
    alumni_count = db.Column(db.Integer, default=0)
    accreditation = db.Column(db.String(50), default="-")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class PPDBRegistration(db.Model):
    __tablename__ = "ppdb_registrations"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(120), default="")
    level = db.Column(db.String(80), default="SMP")
    program = db.Column(db.String(120), default="Full Day")
    notes = db.Column(db.String(300), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class ManagedPage(db.Model):
    __tablename__ = "managed_pages"
    id = db.Column(db.Integer, primary_key=True)
    page_key = db.Column(db.String(50), unique=True, nullable=False, index=True)  # akademik / kesiswaan
    title = db.Column(db.String(200), nullable=False, default="")
    subtitle = db.Column(db.Text, default="")
    content = db.Column(db.Text, default="")
    points = db.Column(db.Text, default="")  # newline-separated items
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactInfo(db.Model):
    __tablename__ = "contact_info"
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.Text, default="")
    email = db.Column(db.String(120), default="")
    phone = db.Column(db.String(50), default="")
    whatsapp = db.Column(db.String(50), default="")
    map_embed_url = db.Column(db.Text, default="")
    instagram_url = db.Column(db.String(255), default="")
    facebook_url = db.Column(db.String(255), default="")
    tiktok_url = db.Column(db.String(255), default="")
    youtube_url = db.Column(db.String(255), default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PPDBProgram(db.Model):
    __tablename__ = "ppdb_programs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    levels = db.Column(db.String(120), default="")
    description = db.Column(db.Text, default="")
    external_url = db.Column(db.String(255), default="")
    sort_order = db.Column(db.Integer, default=0, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
