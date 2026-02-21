from types import SimpleNamespace

from flask import Blueprint, redirect, render_template, url_for
from app.models import ManagedPage

academic_bp = Blueprint("academic", __name__)

ACADEMIC_SECTIONS = {
    "akademik_sbq": {
        "endpoint": "academic.sbq",
        "label": "SBQ",
        "title": "SBQ",
    },
    "akademik_rumah_quran": {
        "endpoint": "academic.rumah_quran",
        "label": "Rumah Qur'an",
        "title": "Rumah Qur'an",
    },
    "akademik_takhosus": {
        "endpoint": "academic.takhosus",
        "label": "Takhosus",
        "title": "Takhosus",
    },
    "akademik_majelis_talim": {
        "endpoint": "academic.majelis_talim",
        "label": "Majelis Ta'lim",
        "title": "Majelis Ta'lim",
    },
}


def _render_section(page_key):
    section = ACADEMIC_SECTIONS[page_key]
    page = ManagedPage.query.filter_by(page_key=page_key).first()

    if page_key == "akademik_sbq":
        default_sbq_subtitle = "Program Sekolah Bina Qur'an untuk penguatan adab, ilmu, dan hafalan."
        default_sbq_content = "Konten SBQ dapat Anda kelola dari dashboard admin."
        page_subtitle = (page.subtitle if page else "").strip()
        page_content = (page.content if page else "").strip()
        page_is_default = (
            page_subtitle in ("", default_sbq_subtitle)
            and page_content in ("", default_sbq_content)
        )
        if page_is_default:
            legacy_page = ManagedPage.query.filter_by(page_key="akademik").first()
            if legacy_page:
                page = legacy_page

    if not page:
        page = SimpleNamespace(
            title=section["title"],
            subtitle="-",
            content="-",
        )

    section_links = [
        {
            "label": item["label"],
            "endpoint": item["endpoint"],
            "active": key == page_key,
        }
        for key, item in ACADEMIC_SECTIONS.items()
    ]
    return render_template(
        "academic/index.html",
        page=page,
        section_links=section_links,
    )


@academic_bp.route("/")
def index():
    return redirect(url_for("academic.sbq"))


@academic_bp.route("/sbq")
def sbq():
    return _render_section("akademik_sbq")


@academic_bp.route("/rumah-quran")
def rumah_quran():
    return _render_section("akademik_rumah_quran")


@academic_bp.route("/takhosus")
def takhosus():
    return _render_section("akademik_takhosus")


@academic_bp.route("/majelis-talim")
def majelis_talim():
    return _render_section("akademik_majelis_talim")
