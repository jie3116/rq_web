from flask import Blueprint, redirect, current_app, render_template
from app.models import PPDBProgram

ppdb_bp = Blueprint("ppdb", __name__)

@ppdb_bp.route("/")
def index():
    programs = (PPDBProgram.query
                .filter_by(is_active=True)
                .order_by(PPDBProgram.sort_order.asc(), PPDBProgram.id.asc())
                .all())
    return render_template("ppdb/index.html", programs=programs)

@ppdb_bp.route("/daftar")
def register():
    return redirect(current_app.config["PPDB_SYSTEM_URL"], code=302)
