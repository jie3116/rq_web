from flask import Blueprint, render_template
from app.models import SiteSetting, GalleryItem

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/")
def about():
    setting = SiteSetting.query.first()
    galleries = (GalleryItem.query
                 .filter_by(category="Profil")
                 .order_by(GalleryItem.created_at.desc())
                 .limit(24).all())
    return render_template("profile/about.html", setting=setting, galleries=galleries)
