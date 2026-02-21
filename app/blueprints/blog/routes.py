from flask import Blueprint, render_template, abort
from app.models import BlogPost

blog_bp = Blueprint("blog", __name__)

@blog_bp.route("/")
def index():
    posts = (BlogPost.query
             .filter_by(is_published=True)
             .order_by(BlogPost.published_at.desc()).all())
    return render_template("blog/index.html", posts=posts)

@blog_bp.route("/<slug>")
def detail(slug):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first()
    if not post:
        abort(404)
    return render_template("blog/detail.html", post=post)
