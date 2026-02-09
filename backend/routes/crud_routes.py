from __future__ import annotations

from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session

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
    next_page = request.args.get("next") or request.form.get("next") or ""

    if request.method == "POST":
        username = (request.form.get("UserName") or "").strip()
        password = (request.form.get("Password") or "").strip()

        if not username or not password:
            flash("Usuario y contraseña son obligatorios", "danger")
            return render_template("login.html", next_page=next_page)

        try:
            with get_connection(current_app) as cn:
                cur = cn.cursor(dictionary=True)
                cur.execute(
                    "SELECT IdUsuario, Nombre, Rol FROM usuarios WHERE Nombre=%s AND Password=%s",
                    (username, password),
                )
                user = cur.fetchone()
                cur.close()
        except Exception as ex:
            flash(f"Error al conectar con la base de datos: {ex}", "danger")
            return render_template("login.html", next_page=next_page)

        if not user:
            flash("Usuario o contraseña incorrectos", "danger")
            return render_template("login.html", next_page=next_page)

        # Validar que el rol del usuario coincida con el módulo al que intenta acceder
        requested_path = next_page or ""
        if requested_path.startswith("/medicos") and user["Rol"] not in (1, 2):
            flash("Las credenciales ingresadas pertenecen a un usuario que no es Médico.", "danger")
            return render_template("login.html", next_page=next_page)

        if requested_path.startswith("/usuarios") and user["Rol"] != 1:
            flash("Las credenciales ingresadas pertenecen a un usuario que no es Administrador.", "danger")
            return render_template("login.html", next_page=next_page)

        if requested_path.startswith("/pacientes") and user["Rol"] != 3:
            flash("Las credenciales ingresadas pertenecen a un usuario que no es Paciente.", "danger")

            return render_template("login.html", next_page=next_page)

        session["user_id"] = user["IdUsuario"]
        session["user_name"] = user["Nombre"]
        role = user["Rol"]
        session["user_role"] = role

        # Mensaje genérico solo para roles no paciente
        if role != 3:
            flash("Inicio de sesión exitoso", "success")

        if next_page:
            # Si es administrador y venía al módulo Usuarios,
            # lo enviamos al nuevo dashboard de administrador.
            if role == 1 and next_page.startswith("/usuarios"):
                return redirect(url_for("crud.admin"))
            return redirect(next_page)

        # Redirección por rol si no se indicó módulo
        if role == 3:
            return redirect(url_for("crud.pacientes"))
        if role == 2:
            return redirect(url_for("crud.medicos"))
        if role == 1:
            # Administrador: llevar al dashboard de administrador
            return redirect(url_for("crud.admin"))

        return redirect(url_for("crud.index"))

    return render_template("login.html", next_page=next_page)


@bp.get("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("crud.index"))


@bp.route("/register", methods=["GET", "POST"], strict_slashes=False)
def register():
    if request.method == "POST":
        return render_template("register.html")
    return render_template("register.html")


@bp.route("/usuarios", methods=["GET", "POST"], strict_slashes=False)
def usuarios():
    # Módulo administrador: requiere login como rol Administrador (1)
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 1:
        flash("No tiene permiso para acceder al módulo Administrador", "danger")
        return redirect(url_for("crud.index"))

    return _handle_model(Usuario)


@bp.route("/admin", methods=["GET", "POST"], strict_slashes=False)
def admin():
    """Dashboard del rol Administrador.

    Muestra un saludo de bienvenida y pestañas para ir a cada módulo de
    administración (usuarios, roles, pacientes, médicos, especialidades,
    medicamentos).
    """

    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 1:
        flash("No tiene permiso para acceder al módulo Administrador", "danger")
        return redirect(url_for("crud.index"))

    # Determinar qué módulo está activo en el dashboard
    module = request.args.get("m", "usuarios")
    d_param = request.args.get("d", "")

    def handle_model(model, active: bool):
        """Versión interna de _handle_model adaptada al dashboard admin.

        Si el módulo está activo, permite operaciones con d/base64 y POST.
        Si no está activo, solo devuelve el listado.
        """

        # Solo el módulo activo procesa POST y parámetro d
        if not active:
            return model.get_list()

        if request.method == "POST":
            msg = model.save(request.form)
            return msg + model.get_list()

        d = d_param
        if d:
            try:
                op, id_ = model._d_decode(d)
            except Exception:
                return model._msg_error("Parámetro d inválido") + model.get_list()

            if op == "new":
                return model.get_form(0)
            if op == "act":
                return model.get_form(id_)
            if op == "det":
                return model.get_detail(id_)
            if op == "del":
                msg = model.delete(id_)
                return msg + model.get_list()

            return model._msg_error("Operación no permitida") + model.get_list()

        return model.get_list()

    # Cargar tablas de cada módulo utilizando los modelos existentes
    with get_connection(current_app) as cn:
        usuarios_model = Usuario(cn)
        roles_model = Rol(cn)
        pacientes_model = Paciente(cn)
        medicos_model = Medico(cn)
        especialidades_model = Especialidad(cn)
        medicamentos_model = Medicamento(cn)

        usuarios_html = handle_model(usuarios_model, module == "usuarios")
        roles_html = handle_model(roles_model, module == "roles")
        pacientes_html = handle_model(pacientes_model, module == "pacientes")
        medicos_html = handle_model(medicos_model, module == "medicos")
        especialidades_html = handle_model(especialidades_model, module == "especialidades")
        medicamentos_html = handle_model(medicamentos_model, module == "medicamentos")

    # Reescribir enlaces para que las acciones sigan dentro de /admin
    usuarios_html = usuarios_html.replace("/usuarios?d=", "/admin?m=usuarios&d=")
    usuarios_html = usuarios_html.replace("href='/usuarios'", "href='/admin?m=usuarios'")

    roles_html = roles_html.replace("/roles?d=", "/admin?m=roles&d=")
    roles_html = roles_html.replace("href='/roles'", "href='/admin?m=roles'")

    pacientes_html = pacientes_html.replace("/pacientes?d=", "/admin?m=pacientes&d=")
    pacientes_html = pacientes_html.replace("href='/pacientes'", "href='/admin?m=pacientes'")

    medicos_html = medicos_html.replace("/medicos?d=", "/admin?m=medicos&d=")
    medicos_html = medicos_html.replace("href='/medicos'", "href='/admin?m=medicos'")

    especialidades_html = especialidades_html.replace("/especialidades?d=", "/admin?m=especialidades&d=")
    especialidades_html = especialidades_html.replace("href='/especialidades'", "href='/admin?m=especialidades'")

    medicamentos_html = medicamentos_html.replace("/medicamentos?d=", "/admin?m=medicamentos&d=")
    medicamentos_html = medicamentos_html.replace("href='/medicamentos'", "href='/admin?m=medicamentos'")

    return render_template(
        "admin_dashboard.html",
        usuarios_html=usuarios_html,
        roles_html=roles_html,
        pacientes_html=pacientes_html,
        medicos_html=medicos_html,
        especialidades_html=especialidades_html,
        medicamentos_html=medicamentos_html,
        active_module=module,
    )


@bp.route("/roles", methods=["GET", "POST"], strict_slashes=False)
def roles():
    # Solo administradores
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 1:
        flash("No tiene permiso para acceder al módulo Roles", "danger")
        return redirect(url_for("crud.index"))

    return _handle_model(Rol)


@bp.route("/pacientes", methods=["GET", "POST"], strict_slashes=False)
def pacientes():
    # Si no hay sesión, primero mostrar formulario de login
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    user_id = session.get("user_id")
    user_role = session.get("user_role")

    # Administrador: CRUD completo de pacientes
    if user_role == 1:
        return _handle_model(Paciente)

    # Paciente: dashboard de solo lectura vinculado a su usuario
    if user_role == 3:
        with get_connection(current_app) as cn:
            cur = cn.cursor(dictionary=True)

            # Datos personales del paciente vinculado al usuario
            cur.execute("SELECT * FROM pacientes WHERE IdUsuario=%s", (user_id,))
            paciente_row = cur.fetchone()

            # Si el usuario logeado no tiene registro en pacientes, no puede entrar al módulo
            if not paciente_row:
                cur.close()
                flash("No tiene permiso para acceder al módulo Paciente", "danger")
                return redirect(url_for("crud.index"))

            paciente_id = paciente_row["IdPaciente"]

            # Mis consultas (solo las del paciente actual)
            consultas = []
            recetas = []
            if paciente_id is not None:
                cur.execute(
                    "SELECT c.IdConsulta, c.FechaConsulta, c.HI, c.HF, c.Diagnostico, "
                    "m.Nombre AS NombreMedico "
                    "FROM consultas c "
                    "LEFT JOIN medicos m ON c.IdMedico = m.IdMedico "
                    "WHERE c.IdPaciente=%s ORDER BY c.FechaConsulta DESC",
                    (paciente_id,),
                )
                consultas = cur.fetchall() or []

                # Mis recetas vinculadas a las consultas del paciente
                cur.execute(
                    "SELECT r.IdReceta, r.Cantidad, "
                    "c.FechaConsulta, c.Diagnostico, "
                    "med.Nombre AS NombreMedico, m2.Nombre AS NombreMedicamento "
                    "FROM recetas r "
                    "LEFT JOIN consultas c ON r.IdConsulta = c.IdConsulta "
                    "LEFT JOIN medicos med ON c.IdMedico = med.IdMedico "
                    "LEFT JOIN medicamentos m2 ON r.IdMedicamento = m2.IdMedicamento "
                    "WHERE c.IdPaciente=%s",
                    (paciente_id,),
                )
                recetas = cur.fetchall() or []

            # Sección de agendar citas (solo lectura: se muestran especialidades y franjas)
            cur.execute("SELECT * FROM especialidades ORDER BY Descripcion")
            especialidades = cur.fetchall() or []

            cur.close()

        return render_template(
            "paciente_dashboard.html",
            paciente=paciente_row,
            consultas=consultas,
            recetas=recetas,
            especialidades=especialidades,
        )

    flash("No tiene permiso para acceder al módulo Paciente", "danger")
    return redirect(url_for("crud.index"))


@bp.route("/medicos", methods=["GET", "POST"], strict_slashes=False)
def medicos():
    # Si no hay sesión, primero mostrar formulario de login
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    user_role = session.get("user_role")
    user_id = session.get("user_id")

    # Administrador: mantiene el CRUD completo de médicos
    if user_role == 1:
        return _handle_model(Medico)

    # Médico: ver su propio panel (similar a paciente)
    if user_role == 2:
        with get_connection(current_app) as cn:
            cur = cn.cursor(dictionary=True)

            # Datos del médico vinculado al usuario logueado (con nombre de especialidad)
            cur.execute(
                "SELECT m.IdMedico, m.Nombre, m.Especialidad, m.IdUsuario, m.Foto, "
                "e.Descripcion AS NombreEspecialidad "
                "FROM medicos m "
                "LEFT JOIN especialidades e ON m.Especialidad = e.IdEsp "
                "WHERE m.IdUsuario=%s",
                (user_id,),
            )
            medico_row = cur.fetchone()

            if not medico_row:
                cur.close()
                flash("No tiene un registro de médico asociado a este usuario", "danger")
                return redirect(url_for("crud.index"))

            medico_id = medico_row["IdMedico"]

            consultas = []
            recetas = []

            # Consultas realizadas por este médico
            cur.execute(
                "SELECT c.IdConsulta, c.FechaConsulta, c.HI, c.HF, c.Diagnostico, "
                "p.Nombre AS NombrePaciente "
                "FROM consultas c "
                "LEFT JOIN pacientes p ON c.IdPaciente = p.IdPaciente "
                "WHERE c.IdMedico=%s ORDER BY c.FechaConsulta DESC",
                (medico_id,),
            )
            consultas = cur.fetchall() or []

            # Recetas emitidas por este médico (a través de sus consultas)
            cur.execute(
                "SELECT r.IdReceta, r.Cantidad, "
                "c.FechaConsulta, c.Diagnostico, "
                "m2.Nombre AS NombreMedicamento, p.Nombre AS NombrePaciente "
                "FROM recetas r "
                "LEFT JOIN consultas c ON r.IdConsulta = c.IdConsulta "
                "LEFT JOIN medicamentos m2 ON r.IdMedicamento = m2.IdMedicamento "
                "LEFT JOIN pacientes p ON c.IdPaciente = p.IdPaciente "
                "WHERE c.IdMedico=%s",
                (medico_id,),
            )
            recetas = cur.fetchall() or []

            cur.close()

        return render_template(
            "medico_dashboard.html",
            medico=medico_row,
            consultas=consultas,
            recetas=recetas,
        )

    flash("No tiene permiso para acceder al módulo Médico", "danger")
    return redirect(url_for("crud.index"))


@bp.route("/especialidades", methods=["GET", "POST"], strict_slashes=False)
def especialidades():
    # Solo administradores
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 1:
        flash("No tiene permiso para acceder al módulo Especialidades", "danger")
        return redirect(url_for("crud.index"))

    return _handle_model(Especialidad)


@bp.route("/medicamentos", methods=["GET", "POST"], strict_slashes=False)
def medicamentos():
    # Solo administradores
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 1:
        flash("No tiene permiso para acceder al módulo Medicamentos", "danger")
        return redirect(url_for("crud.index"))

    return _handle_model(Medicamento)


@bp.route("/consultas", methods=["GET", "POST"], strict_slashes=False)
def consultas():
    return _handle_model(Consulta)


@bp.route("/recetas", methods=["GET", "POST"], strict_slashes=False)
def recetas():
    return _handle_model(Receta)
