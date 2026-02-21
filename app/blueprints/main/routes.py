from urllib.parse import parse_qs, urlparse

from flask import Blueprint, render_template
from app.models import Announcement, SiteStat, Testimonial, GalleryItem, VideoProfile, SiteSetting, BlogPost

main_bp = Blueprint("main", __name__)


def _extract_youtube_video_id(value):
    raw = (value or "").strip()
    if not raw:
        return ""

    parsed = urlparse(raw)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    if "youtube.com" in host and "embed/" in parsed.path:
        return path.split("embed/", 1)[1].split("/")[0]

    if "youtu.be" in host:
        return path.split("/")[0]

    if "youtube.com" in host:
        if parsed.path.startswith("/watch"):
            return parse_qs(parsed.query).get("v", [""])[0]
        if parsed.path.startswith("/shorts/"):
            return path.split("shorts/", 1)[1].split("/")[0]

    return ""


def _youtube_embed_url(value):
    video_id = _extract_youtube_video_id(value)
    if not video_id:
        return ""
    return f"https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1&playsinline=1"


def _youtube_thumbnail_url(value):
    video_id = _extract_youtube_video_id(value)
    if not video_id:
        return ""
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


@main_bp.route("/")
def home():
    announcements = (Announcement.query
                     .filter_by(is_published=True)
                     .order_by(Announcement.published_at.desc())
                     .limit(3).all())

    stats = SiteStat.query.order_by(SiteStat.updated_at.desc()).first()
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).limit(6).all()
    hero_slides = (GalleryItem.query
                   .filter_by(category="Hero")
                   .order_by(GalleryItem.created_at.desc())
                   .limit(5).all())
    teacher_photos = (GalleryItem.query
                      .filter_by(category="Guru")
                      .order_by(GalleryItem.created_at.desc())
                      .limit(12).all())
    teacher_cards = []
    for item in teacher_photos:
        raw_title = (item.title or "").strip()
        name = raw_title
        subject = "Belum diisi"
        if "|" in raw_title:
            left, right = raw_title.split("|", 1)
            name = left.strip() or "Guru"
            subject = right.strip() or "Belum diisi"
        elif " - " in raw_title:
            left, right = raw_title.split(" - ", 1)
            name = left.strip() or "Guru"
            subject = right.strip() or "Belum diisi"
        elif not raw_title:
            name = "Guru"
        teacher_cards.append({
            "image_url": item.image_url,
            "name": name,
            "subject": subject,
        })
    gallery_kegiatan = (GalleryItem.query
                        .filter_by(category="Kegiatan")
                        .order_by(GalleryItem.created_at.desc())
                        .limit(8).all())
    gallery_fasilitas = (GalleryItem.query
                         .filter_by(category="Fasilitas")
                         .order_by(GalleryItem.created_at.desc())
                         .limit(8).all())
    video = VideoProfile.query.order_by(VideoProfile.created_at.desc()).first()
    video_embed_url = _youtube_embed_url(video.youtube_embed_url if video else "")
    video_thumbnail_url = _youtube_thumbnail_url(video.youtube_embed_url if video else "")
    setting = SiteSetting.query.first()

    latest_posts = (BlogPost.query
                    .filter_by(is_published=True)
                    .order_by(BlogPost.published_at.desc())
                    .limit(3).all())

    return render_template(
        "main/home.html",
        announcements=announcements,
        stats=stats,
        testimonials=testimonials,
        hero_slides=hero_slides,
        teacher_cards=teacher_cards,
        gallery_kegiatan=gallery_kegiatan,
        gallery_fasilitas=gallery_fasilitas,
        video=video,
        video_embed_url=video_embed_url,
        video_thumbnail_url=video_thumbnail_url,
        setting=setting,
        latest_posts=latest_posts
    )
