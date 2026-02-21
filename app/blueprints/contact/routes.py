from flask import Blueprint, render_template
from app.models import ContactInfo

contact_bp = Blueprint("contact", __name__)

@contact_bp.route("/")
def index():
    info = ContactInfo.query.first()
    return render_template("contact/index.html", info=info)
