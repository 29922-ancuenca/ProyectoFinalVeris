from flask import Blueprint, flash, redirect, render_template, request, url_for

bp = Blueprint("views", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/login")
def login():
    return render_template("login.html")


@bp.post("/login")
def login_post():
    # Vista implementada; autenticación real se puede agregar luego.
    username = request.form.get("UserName", "")
    flash(f"Login de '{username}' (demo): pendiente de implementar", "warning")
    return redirect(url_for("views.index"))


@bp.get("/register")
def register():
    return render_template("register.html")


@bp.post("/register")
def register_post():
    username = request.form.get("UserName", "")
    flash(f"Registro de '{username}' (demo): pendiente de implementar", "warning")
    return redirect(url_for("views.login"))
