from __future__ import annotations

from flask import Blueprint, current_app, render_template, request

from database.connection import get_connection

from models.consulta import Consulta
from models.especialidad import Especialidad
from models.medicamento import Medicamento
from models.medico import Medico
from models.paciente import Paciente
from models.receta import Receta
from models.rol import Rol
from models.usuario import Usuario


bp = Blueprint("crud", __name__)


def _render_crud_page(model, content_html: str):
    return render_template(
        "base.html",
        navbar_html=model.navbar(),
        content_html=content_html,
        page_title=model.title,
    )


def _handle_model(ModelClass):
    """Manejador genérico para GET/POST usando navegación d=base64(op/id)."""

    with get_connection(current_app) as cn:
        model = ModelClass(cn)

        if request.method == "POST":
            msg = model.save(request.form)
            return _render_crud_page(model, msg + model.get_list())

        d = request.args.get("d", "")
        if d:
            try:
                op, id_ = model._d_decode(d)
            except Exception:
                return _render_crud_page(model, model._msg_error("Parámetro d inválido") + model.get_list())

            if op == "new":
                return _render_crud_page(model, model.get_form(0))
            if op == "act":
                return _render_crud_page(model, model.get_form(id_))
            if op == "det":
                return _render_crud_page(model, model.get_detail(id_))
            if op == "del":
                msg = model.delete(id_)
                return _render_crud_page(model, msg + model.get_list())

            return _render_crud_page(model, model._msg_error("Operación no permitida") + model.get_list())

        return _render_crud_page(model, model.get_list())


@bp.get("/")
def index():
    # Landing simple (usa templates existentes)
    return render_template("index.html")


@bp.route("/login", methods=["GET", "POST"], strict_slashes=False)
def login():
    if request.method == "POST":
        # Demo: autenticación real queda fuera del alcance del CRUD
        return render_template("login.html")
    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"], strict_slashes=False)
def register():
    if request.method == "POST":
        return render_template("register.html")
    return render_template("register.html")


@bp.route("/usuarios", methods=["GET", "POST"], strict_slashes=False)
def usuarios():
    return _handle_model(Usuario)


@bp.route("/roles", methods=["GET", "POST"], strict_slashes=False)
def roles():
    return _handle_model(Rol)


@bp.route("/pacientes", methods=["GET", "POST"], strict_slashes=False)
def pacientes():
    return _handle_model(Paciente)


@bp.route("/medicos", methods=["GET", "POST"], strict_slashes=False)
def medicos():
    return _handle_model(Medico)


@bp.route("/especialidades", methods=["GET", "POST"], strict_slashes=False)
def especialidades():
    return _handle_model(Especialidad)


@bp.route("/medicamentos", methods=["GET", "POST"], strict_slashes=False)
def medicamentos():
    return _handle_model(Medicamento)


@bp.route("/consultas", methods=["GET", "POST"], strict_slashes=False)
def consultas():
    return _handle_model(Consulta)


@bp.route("/recetas", methods=["GET", "POST"], strict_slashes=False)
def recetas():
    return _handle_model(Receta)
