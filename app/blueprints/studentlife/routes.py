from types import SimpleNamespace

from flask import Blueprint, redirect, render_template, url_for
from app.models import ManagedPage

studentlife_bp = Blueprint("studentlife", __name__)

STUDENTLIFE_SECTIONS = {
    "kesiswaan_daily_activity": {
        "endpoint": "studentlife.daily_activity",
        "label": "Daily Activity",
        "title": "Daily Activity",
    },
    "kesiswaan_ekstrakulikuler": {
        "endpoint": "studentlife.ekstrakulikuler",
        "label": "Ekstrakulikuler",
        "title": "Ekstrakulikuler",
    },
    "kesiswaan_organisasi_santri": {
        "endpoint": "studentlife.organisasi_santri",
        "label": "Organisasi Santri",
        "title": "Organisasi Santri",
    },
}


def _render_section(page_key):
    section = STUDENTLIFE_SECTIONS[page_key]
    page = ManagedPage.query.filter_by(page_key=page_key).first()
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
        for key, item in STUDENTLIFE_SECTIONS.items()
    ]
    return render_template(
        "studentlife/index.html",
        page=page,
        section_links=section_links,
    )


@studentlife_bp.route("/")
def index():
    return redirect(url_for("studentlife.daily_activity"))


@studentlife_bp.route("/daily-activity")
def daily_activity():
    return _render_section("kesiswaan_daily_activity")


@studentlife_bp.route("/ekstrakulikuler")
def ekstrakulikuler():
    return _render_section("kesiswaan_ekstrakulikuler")


@studentlife_bp.route("/organisasi-santri")
def organisasi_santri():
    return _render_section("kesiswaan_organisasi_santri")
