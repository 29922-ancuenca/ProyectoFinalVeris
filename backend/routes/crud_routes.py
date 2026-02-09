from __future__ import annotations

import calendar as pycalendar
from pathlib import Path
from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

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


_MAX_AGENDAR_FECHA = date(2030, 12, 31)


def _parse_int(value: str | None, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return default


def _time_to_minutes(value) -> int:
    """Convierte MySQL TIME (str o datetime.time) a minutos desde medianoche."""

    if value is None:
        return 0
    if hasattr(value, "hour") and hasattr(value, "minute"):
        return int(value.hour) * 60 + int(value.minute)
    s = str(value)
    # soporta HH:MM o HH:MM:SS
    parts = s.split(":")
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    return h * 60 + m


def _minutes_to_hhmm(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def _dias_str_to_weekdays(dias: str) -> set[int]:
    """Mapea Dias (L M X J V S D) a weekday() de Python (Lunes=0..Domingo=6)."""

    mapping = {"L": 0, "M": 1, "X": 2, "J": 3, "V": 4, "S": 5, "D": 6}
    return {mapping[c] for c in (dias or "") if c in mapping}


def _month_name_es(month: int) -> str:
    meses = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    try:
        return meses[month - 1].capitalize()
    except Exception:
        return ""


def _build_calendar(anio: int, mes: int, today: date, selected_iso: str | None, dias_con_horarios: dict[str, int]):
    """Devuelve semanas con celdas listas para render en Jinja."""

    cal = pycalendar.Calendar(firstweekday=0)  # Lunes
    weeks = []
    selected = selected_iso or ""

    for week in cal.monthdatescalendar(anio, mes):
        row = []
        for d in week:
            if d.month != mes:
                row.append({"empty": True})
                continue

            iso = d.isoformat()
            is_past = d < today
            count = int(dias_con_horarios.get(iso, 0))
            has_slots = (not is_past) and (count > 0)
            row.append(
                {
                    "empty": False,
                    "iso": iso,
                    "day": d.day,
                    "is_past": is_past,
                    "has_slots": has_slots,
                    "slot_count": count,
                    "is_selected": iso == selected,
                }
            )
        weeks.append(row)

    return weeks


def _get_paciente_id_for_user(cn, user_id: int) -> int | None:
    cur = cn.cursor(dictionary=True)
    cur.execute("SELECT IdPaciente FROM pacientes WHERE IdUsuario=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return row.get("IdPaciente")


def _get_available_slots_30m(cn, id_medico: int, fecha_iso: str, franja_hi, franja_hf) -> list[str]:
    """Calcula horarios disponibles (inicio) en intervalos de 30 min."""

    start_min = _time_to_minutes(franja_hi)
    end_min = _time_to_minutes(franja_hf)
    slot_len = 30

    if end_min <= start_min:
        return []

    # Generar candidatos
    candidates: list[tuple[int, int]] = []
    m = start_min
    while m + slot_len <= end_min:
        candidates.append((m, m + slot_len))
        m += slot_len

    # Ocupados por consultas existentes
    cur = cn.cursor(dictionary=True)
    cur.execute(
        "SELECT HI, HF FROM consultas WHERE IdMedico=%s AND FechaConsulta=%s",
        (id_medico, fecha_iso),
    )
    busy_rows = cur.fetchall() or []
    cur.close()

    busy: list[tuple[int, int]] = []
    for r in busy_rows:
        hi = _time_to_minutes(r.get("HI"))
        hf = _time_to_minutes(r.get("HF"))
        if hf > hi:
            busy.append((hi, hf))

    def overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
        return a[0] < b[1] and a[1] > b[0]

    available = []
    for c in candidates:
        if any(overlaps(c, b) for b in busy):
            continue
        available.append(_minutes_to_hhmm(c[0]))

    return available


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

        # Validar que el rol del usuario coincida con el módulo al que intenta acceder.
        requested_path = next_page or ""
        if requested_path.startswith("/medicos") and user["Rol"] != 2:
            flash("Las credenciales ingresadas pertenecen a un usuario que no es Médico.", "danger")
            return render_template("login.html", next_page=next_page)

        if requested_path.startswith("/pacientes") and user["Rol"] != 3:
            flash("Las credenciales ingresadas pertenecen a un usuario que no es Paciente.", "danger")
            return render_template("login.html", next_page=next_page)

        if requested_path.startswith("/usuarios") and user["Rol"] != 1:
            flash("Las credenciales ingresadas pertenecen a un usuario que no es Administrador.", "danger")
            return render_template("login.html", next_page=next_page)

        if requested_path.startswith("/roles") and user["Rol"] != 1:
            flash("Las credenciales ingresadas pertenecen a un usuario que no es Administrador.", "danger")
            return render_template("login.html", next_page=next_page)

        if requested_path.startswith("/especialidades") and user["Rol"] != 1:
            flash("Las credenciales ingresadas pertenecen a un usuario que no es Administrador.", "danger")
            return render_template("login.html", next_page=next_page)

        if requested_path.startswith("/medicamentos") and user["Rol"] != 1:
            flash("Las credenciales ingresadas pertenecen a un usuario que no es Administrador.", "danger")
            return render_template("login.html", next_page=next_page)

        session["user_id"] = user["IdUsuario"]
        session["user_name"] = user["Nombre"]
        role = user["Rol"]
        session["user_role"] = role

        # Mensaje genérico solo para roles no paciente
        if role != 3:
            flash("Inicio de sesión exitoso", "success")

        if next_page:
            # Si es administrador, todo se gestiona desde /admin.
            if role == 1:
                if next_page.startswith("/usuarios"):
                    return redirect(url_for("crud.admin", m="usuarios"))
                if next_page.startswith("/roles"):
                    return redirect(url_for("crud.admin", m="roles"))
                if next_page.startswith("/pacientes"):
                    return redirect(url_for("crud.admin", m="pacientes"))
                if next_page.startswith("/medicos"):
                    return redirect(url_for("crud.admin", m="medicos"))
                if next_page.startswith("/especialidades"):
                    return redirect(url_for("crud.admin", m="especialidades"))
                if next_page.startswith("/medicamentos"):
                    return redirect(url_for("crud.admin", m="medicamentos"))
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
    def validar_cedula_ec(cedula: str) -> bool:
        c = (cedula or "").strip()
        if len(c) != 10 or not c.isdigit():
            return False

        # La columna `Cedula` está definida como INT UNSIGNED.
        # Evitar intentar insertar valores fuera de rango (provoca error 1264).
        try:
            if int(c) > 4294967295:
                return False
        except Exception:
            return False

        total = 0
        for i in range(9):
            digit = int(c[i])
            if i % 2 == 0:
                mul = digit * 2
                total += (mul - 9) if mul > 9 else mul
            else:
                total += digit
        last = int(c[9])
        mod = total % 10
        return (mod == 0 and last == 0) or ((10 - mod) == last)

    def validar_nombre_paciente(nombre: str) -> bool:
        n = " ".join((nombre or "").strip().split())
        parts = [p for p in n.split(" ") if p]
        if len(parts) != 2:
            return False
        import re

        rx = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ]+$")
        if not all(rx.match(p) for p in parts):
            return False
        return all(p[0].isupper() for p in parts)

    def validar_nombre_medico(nombre: str) -> bool:
        n = (nombre or "").strip()
        if not n.startswith("Dr/a. "):
            return False
        body = n[len("Dr/a. ") :].strip()
        parts = [p for p in body.split(" ") if p]
        if len(parts) != 2:
            return False
        import re

        rx = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ]+$")
        if not all(rx.match(p) for p in parts):
            return False
        return all(p[0].isupper() for p in parts)

    def load_form_data():
        with get_connection(current_app) as cn:
            cur = cn.cursor(dictionary=True)
            cur.execute("SELECT IdRol, Nombre FROM roles WHERE IdRol IN (2,3) ORDER BY IdRol")
            roles = cur.fetchall() or []
            cur.execute("SELECT IdEsp, Descripcion FROM especialidades ORDER BY Descripcion")
            especialidades = cur.fetchall() or []
            cur.close()
        return roles, especialidades

    if request.method == "GET":
        roles, especialidades = load_form_data()
        return render_template("register.html", roles=roles, especialidades=especialidades)

    # POST
    username = (request.form.get("UserName") or "").strip()
    password = (request.form.get("Password") or "").strip()
    rol_s = (request.form.get("Rol") or "").strip()
    try:
        rol = int(rol_s)
    except Exception:
        rol = 0

    roles, especialidades = load_form_data()

    if not username or not password:
        flash("Usuario y contraseña son obligatorios", "danger")
        return render_template("register.html", roles=roles, especialidades=especialidades)

    if rol not in (2, 3):
        flash("Debe seleccionar un rol (Médico o Paciente)", "danger")
        return render_template("register.html", roles=roles, especialidades=especialidades)

    # Perfil común
    nombre_perfil = (request.form.get("NombrePerfil") or "").strip()
    if not nombre_perfil:
        flash("El nombre completo es obligatorio", "danger")
        return render_template("register.html", roles=roles, especialidades=especialidades)

    # Foto opcional
    foto_filename = ""
    try:
        file = request.files.get("Foto")  # type: ignore[attr-defined]
    except Exception:
        file = None

    filename_raw = (getattr(file, "filename", "") or "") if file else ""
    if file and filename_raw:
        filename = secure_filename(filename_raw)
        if filename:
            upload_dir = Path(current_app.static_folder) / "img" / "usuarios"  # type: ignore[attr-defined]
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / filename
            file.save(str(file_path))
            foto_filename = filename

    try:
        with get_connection(current_app) as cn:
            cur = cn.cursor(dictionary=True)
            # Usuario único por Nombre
            cur.execute("SELECT 1 FROM usuarios WHERE LOWER(Nombre)=LOWER(%s) LIMIT 1", (username,))
            if cur.fetchone():
                cur.close()
                flash("Ese usuario ya existe", "danger")
                return render_template("register.html", roles=roles, especialidades=especialidades)

            # Insert usuario
            cur2 = cn.cursor()
            cur2.execute("INSERT INTO usuarios(Nombre, Password, Rol) VALUES(%s,%s,%s)", (username, password, rol))
            user_id = int(cur2.lastrowid)
            cur2.close()

            if rol == 3:
                cedula = (request.form.get("Cedula") or "").strip()
                edad_s = (request.form.get("Edad") or "").strip()
                genero = (request.form.get("Genero") or "").strip()
                estatura_s = (request.form.get("Estatura_cm") or "").strip()
                peso_s = (request.form.get("Peso_kg") or "").strip()

                try:
                    edad = int(edad_s) if edad_s else None
                except Exception:
                    edad = None
                try:
                    estatura = float(estatura_s) if estatura_s else None
                except Exception:
                    estatura = None
                try:
                    peso = float(peso_s) if peso_s else None
                except Exception:
                    peso = None

                if not validar_nombre_paciente(nombre_perfil):
                    cn.rollback()
                    cur.close()
                    flash("Nombre inválido. Use el formato: Nombre Apellido (solo letras, iniciales en mayúscula)", "danger")
                    return render_template("register.html", roles=roles, especialidades=especialidades)

                if not validar_cedula_ec(cedula):
                    cn.rollback()
                    cur.close()
                    flash("Cédula inválida o fuera de rango. Ingrese una cédula ecuatoriana válida", "danger")
                    return render_template("register.html", roles=roles, especialidades=especialidades)

                if edad is None or edad < 0 or edad > 120:
                    cn.rollback()
                    cur.close()
                    flash("Edad inválida. Debe estar entre 0 y 120", "danger")
                    return render_template("register.html", roles=roles, especialidades=especialidades)

                if genero not in ("Masculino", "Femenino"):
                    cn.rollback()
                    cur.close()
                    flash("Género inválido. Seleccione Masculino o Femenino", "danger")
                    return render_template("register.html", roles=roles, especialidades=especialidades)

                if estatura is not None and (estatura < 30 or estatura > 250):
                    cn.rollback()
                    cur.close()
                    flash("Estatura inválida. Debe estar entre 30 y 250 cm", "danger")
                    return render_template("register.html", roles=roles, especialidades=especialidades)

                if peso is not None and (peso < 0 or peso > 300):
                    cn.rollback()
                    cur.close()
                    flash("Peso inválido. Debe estar entre 0 y 300 kg", "danger")
                    return render_template("register.html", roles=roles, especialidades=especialidades)

                if not cedula or edad is None or not genero:
                    cn.rollback()
                    cur.close()
                    flash("Complete los datos obligatorios del Paciente", "danger")
                    return render_template("register.html", roles=roles, especialidades=especialidades)

                cur.execute(
                    "INSERT INTO pacientes(IdUsuario, Nombre, Cedula, Edad, Genero, `Estatura (cm)`, `Peso (kg)`, Foto) "
                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                    (user_id, nombre_perfil, cedula, edad, genero, estatura, peso, foto_filename),
                )
                cn.commit()
                cur.close()
                flash("Registro de Paciente creado correctamente", "success")
                return redirect(url_for("crud.login"))

            # rol == 2 (Médico)
            if not validar_nombre_medico(nombre_perfil):
                cn.rollback()
                cur.close()
                flash("Nombre inválido. Debe tener el formato: Dr/a. Nombre Apellido", "danger")
                return render_template("register.html", roles=roles, especialidades=especialidades)

            especialidad = (request.form.get("Especialidad") or "").strip()
            if not especialidad:
                cn.rollback()
                cur.close()
                flash("Debe seleccionar una especialidad", "danger")
                return render_template("register.html", roles=roles, especialidades=especialidades)

            cur.execute(
                "INSERT INTO medicos(Nombre, Especialidad, IdUsuario, Foto) VALUES(%s,%s,%s,%s)",
                (nombre_perfil, especialidad, user_id, foto_filename),
            )
            cn.commit()
            cur.close()
            flash("Registro de Médico creado correctamente", "success")
            return redirect(url_for("crud.login"))
    except Exception as ex:
        flash(f"Error al registrar: {ex}", "danger")
        return render_template("register.html", roles=roles, especialidades=especialidades)


@bp.route("/usuarios", methods=["GET", "POST"], strict_slashes=False)
def usuarios():
    # Módulo administrador: requiere login como rol Administrador (1)
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 1:
        flash("No tiene permiso para acceder al módulo Administrador", "danger")
        return redirect(url_for("crud.index"))

    # Todo el módulo Administrador se maneja en /admin
    return redirect(url_for("crud.admin", m="usuarios"))


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

    return redirect(url_for("crud.admin", m="roles"))


@bp.route("/pacientes", methods=["GET", "POST"], strict_slashes=False)
def pacientes():
    # Si no hay sesión, primero mostrar formulario de login
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    user_id = session.get("user_id")
    user_role = session.get("user_role")

    # Administrador: se gestiona desde el dashboard /admin
    if user_role == 1:
        flash("No tiene permiso para acceder al módulo Paciente", "danger")
        return redirect(url_for("crud.admin", m="pacientes"))

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
            consultas_recibidas = []
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

                # Consultas recibidas con receta asignada (indicador de consulta realizada)
                cur.execute(
                    "SELECT c.IdConsulta, c.FechaConsulta, c.HI, c.HF, c.Diagnostico, "
                    "m.Nombre AS NombreMedico "
                    "FROM consultas c "
                    "LEFT JOIN medicos m ON c.IdMedico = m.IdMedico "
                    "WHERE c.IdPaciente=%s "
                    "AND EXISTS (SELECT 1 FROM recetas r WHERE r.IdConsulta = c.IdConsulta) "
                    "ORDER BY c.FechaConsulta DESC",
                    (paciente_id,),
                )
                consultas_recibidas = cur.fetchall() or []

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
            consultas_recibidas=consultas_recibidas,
            recetas=recetas,
            especialidades=especialidades,
        )

    flash("No tiene permiso para acceder al módulo Paciente", "danger")
    return redirect(url_for("crud.index"))


@bp.get("/pacientes/agendar-cita")
def agendar_cita():
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 3:
        flash("No tiene permiso para acceder al agendamiento de citas", "danger")
        return redirect(url_for("crud.index"))

    user_id = int(session.get("user_id"))

    today = date.today()

    # Parámetros de navegación
    mes = _parse_int(request.args.get("mes"), today.month)
    anio = _parse_int(request.args.get("anio"), today.year)

    # Clamp a rango permitido
    if (anio, mes) < (today.year, today.month):
        anio, mes = today.year, today.month
    if (anio, mes) > (_MAX_AGENDAR_FECHA.year, _MAX_AGENDAR_FECHA.month):
        anio, mes = _MAX_AGENDAR_FECHA.year, _MAX_AGENDAR_FECHA.month

    id_especialidad = (request.args.get("idEspecialidad") or "").strip()
    id_medico = (request.args.get("idMedico") or "").strip()
    fecha_sel = (request.args.get("fecha") or "").strip()
    conflict = (request.args.get("conflict") or "").strip()

    # Validar fecha seleccionada
    if fecha_sel:
        try:
            fecha_obj = datetime.strptime(fecha_sel, "%Y-%m-%d").date()
            if fecha_obj < today or fecha_obj > _MAX_AGENDAR_FECHA:
                fecha_sel = ""
        except Exception:
            fecha_sel = ""

    with get_connection(current_app) as cn:
        cur = cn.cursor(dictionary=True)

        # Datos para navbar (paciente)
        cur.execute("SELECT Nombre, Foto FROM pacientes WHERE IdUsuario=%s", (user_id,))
        nav_user = cur.fetchone() or {}

        # Especialidades
        cur.execute("SELECT IdEsp, Descripcion, Dias, Franja_HI, Franja_HF FROM especialidades ORDER BY Descripcion")
        especialidades = cur.fetchall() or []

        # Médicos filtrados por especialidad
        medicos: list[dict] = []
        especialidad_row = None
        if id_especialidad:
            cur.execute(
                "SELECT IdEsp, Descripcion, Dias, Franja_HI, Franja_HF FROM especialidades WHERE IdEsp=%s",
                (id_especialidad,),
            )
            especialidad_row = cur.fetchone()

            cur.execute(
                "SELECT IdMedico, Nombre FROM medicos WHERE Especialidad=%s ORDER BY Nombre",
                (id_especialidad,),
            )
            medicos = cur.fetchall() or []

        # Validar médico dentro de la especialidad
        medico_row = None
        if id_medico and id_especialidad:
            cur.execute(
                "SELECT m.IdMedico, m.Nombre, m.Especialidad, e.Descripcion AS NombreEspecialidad, e.Dias, e.Franja_HI, e.Franja_HF "
                "FROM medicos m LEFT JOIN especialidades e ON m.Especialidad = e.IdEsp "
                "WHERE m.IdMedico=%s AND m.Especialidad=%s",
                (id_medico, id_especialidad),
            )
            medico_row = cur.fetchone()
            if not medico_row:
                id_medico = ""
                fecha_sel = ""

        dias_con_horarios: dict[str, int] = {}
        horarios: list[str] = []

        if medico_row:
            dias_permitidos = _dias_str_to_weekdays(str(medico_row.get("Dias") or ""))
            franja_hi = medico_row.get("Franja_HI")
            franja_hf = medico_row.get("Franja_HF")

            # Para cada día del mes, contar slots
            _, days_in_month = pycalendar.monthrange(anio, mes)
            for day in range(1, days_in_month + 1):
                d = date(anio, mes, day)
                if d < today or d > _MAX_AGENDAR_FECHA:
                    continue
                if dias_permitidos and d.weekday() not in dias_permitidos:
                    continue
                iso = d.isoformat()
                slots = _get_available_slots_30m(cn, int(medico_row["IdMedico"]), iso, franja_hi, franja_hf)

                # Si es hoy, filtrar slots ya pasados
                if d == today:
                    now = datetime.now()
                    now_min = now.hour * 60 + now.minute
                    slots = [s for s in slots if _time_to_minutes(s) > now_min]

                if slots:
                    dias_con_horarios[iso] = len(slots)

            # Horarios del día seleccionado
            if fecha_sel:
                try:
                    dsel = datetime.strptime(fecha_sel, "%Y-%m-%d").date()
                except Exception:
                    dsel = None

                if dsel and (not dias_permitidos or dsel.weekday() in dias_permitidos) and dsel >= today:
                    horarios = _get_available_slots_30m(
                        cn,
                        int(medico_row["IdMedico"]),
                        fecha_sel,
                        franja_hi,
                        franja_hf,
                    )
                    if dsel == today:
                        now = datetime.now()
                        now_min = now.hour * 60 + now.minute
                        horarios = [s for s in horarios if _time_to_minutes(s) > now_min]
                else:
                    fecha_sel = ""

        cur.close()

    calendario = _build_calendar(anio, mes, today, fecha_sel or None, dias_con_horarios)
    nombre_mes = f"{_month_name_es(mes)} {anio}"

    es_primer_mes = (anio, mes) == (today.year, today.month)
    es_ultimo_mes = (anio, mes) == (_MAX_AGENDAR_FECHA.year, _MAX_AGENDAR_FECHA.month)

    return render_template(
        "agendar_cita.html",
        especialidades=especialidades,
        medicos=medicos,
        id_especialidad=id_especialidad,
        id_medico=id_medico,
        mes=mes,
        anio=anio,
        fecha=fecha_sel,
        calendario=calendario,
        dias_con_horarios=dias_con_horarios,
        horarios=horarios,
        nombre_mes=nombre_mes,
        es_primer_mes=es_primer_mes,
        es_ultimo_mes=es_ultimo_mes,
        nav_nombre=(session.get("user_name") or ""),
        nav_foto=(nav_user.get("Foto") or ""),
        conflict_modal_message=(
            "Ya tienes una cita agendada en esa fecha y hora. No puedes agendar otra en ese momento."
            if conflict
            else ""
        ),
    )


@bp.post("/pacientes/agendar-cita/confirmar")
def agendar_cita_confirmar():
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 3:
        flash("No tiene permiso para agendar citas", "danger")
        return redirect(url_for("crud.index"))

    id_especialidad = (request.form.get("IdEspecialidad") or "").strip()
    id_medico = (request.form.get("IdMedico") or "").strip()
    fecha = (request.form.get("FechaConsulta") or "").strip()
    hi = (request.form.get("HI") or "").strip()

    if not (id_especialidad and id_medico and fecha and hi):
        flash("Complete especialidad, médico, fecha y horario.", "warning")
        return redirect(url_for("crud.agendar_cita"))

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except Exception:
        flash("Fecha inválida.", "warning")
        return redirect(url_for("crud.agendar_cita"))

    if fecha_obj < date.today() or fecha_obj > _MAX_AGENDAR_FECHA:
        flash("La fecha seleccionada no está permitida.", "warning")
        return redirect(url_for("crud.agendar_cita"))

    # HF = HI + 30 min
    try:
        hi_min = _time_to_minutes(hi)
        hf_min = hi_min + 30
        hf = _minutes_to_hhmm(hf_min) + ":00"
        hi_db = hi + ":00" if len(hi) == 5 else hi
    except Exception:
        flash("Horario inválido.", "warning")
        return redirect(url_for("crud.agendar_cita"))

    user_id = int(session.get("user_id"))

    with get_connection(current_app) as cn:
        paciente_id = _get_paciente_id_for_user(cn, user_id)
        if not paciente_id:
            flash("No existe un paciente asociado a este usuario.", "danger")
            return redirect(url_for("crud.pacientes"))

        cur = cn.cursor(dictionary=True)
        # Validar médico vs especialidad y obtener franja/días
        cur.execute(
            "SELECT m.IdMedico, m.Nombre, e.Dias, e.Franja_HI, e.Franja_HF "
            "FROM medicos m LEFT JOIN especialidades e ON m.Especialidad = e.IdEsp "
            "WHERE m.IdMedico=%s AND m.Especialidad=%s",
            (id_medico, id_especialidad),
        )
        medico_row = cur.fetchone()
        if not medico_row:
            cur.close()
            flash("El médico no corresponde a la especialidad seleccionada.", "warning")
            return redirect(url_for("crud.agendar_cita", idEspecialidad=id_especialidad))

        dias_permitidos = _dias_str_to_weekdays(str(medico_row.get("Dias") or ""))
        if dias_permitidos and fecha_obj.weekday() not in dias_permitidos:
            cur.close()
            flash("La especialidad no atiende en el día seleccionado.", "warning")
            return redirect(url_for("crud.agendar_cita", idEspecialidad=id_especialidad, idMedico=id_medico))

        franja_hi = medico_row.get("Franja_HI")
        franja_hf = medico_row.get("Franja_HF")
        slots = _get_available_slots_30m(cn, int(medico_row["IdMedico"]), fecha, franja_hi, franja_hf)
        if hi not in slots:
            cur.close()
            flash("El horario seleccionado ya no está disponible.", "warning")
            return redirect(
                url_for(
                    "crud.agendar_cita",
                    idEspecialidad=id_especialidad,
                    idMedico=id_medico,
                    fecha=fecha,
                )
            )

        # Validar choque (doble validación)
        cur.execute(
            "SELECT 1 FROM consultas "
            "WHERE IdMedico=%s AND FechaConsulta=%s "
            "AND NOT (HF <= %s OR HI >= %s) LIMIT 1",
            (id_medico, fecha, hi_db, hf),
        )
        clash = cur.fetchone()
        if clash:
            cur.close()
            flash("Ese horario acaba de ocuparse. Seleccione otro.", "warning")
            return redirect(
                url_for(
                    "crud.agendar_cita",
                    idEspecialidad=id_especialidad,
                    idMedico=id_medico,
                    fecha=fecha,
                )
            )

        # Validar choque del paciente (no puede tener dos citas en el mismo horario)
        cur.execute(
            "SELECT 1 FROM consultas "
            "WHERE IdPaciente=%s AND FechaConsulta=%s "
            "AND NOT (HF <= %s OR HI >= %s) LIMIT 1",
            (paciente_id, fecha, hi_db, hf),
        )
        patient_clash = cur.fetchone()
        if patient_clash:
            cur.close()
            return redirect(
                url_for(
                    "crud.agendar_cita",
                    idEspecialidad=id_especialidad,
                    idMedico=id_medico,
                    fecha=fecha,
                    conflict=1,
                )
            )

        # Insertar consulta con Diagnostico pendiente
        cur.execute(
            "INSERT INTO consultas(IdMedico, IdPaciente, FechaConsulta, HI, HF, Diagnostico) "
            "VALUES(%s,%s,%s,%s,%s,%s)",
            (id_medico, paciente_id, fecha, hi_db, hf, "Pendiente"),
        )
        cn.commit()
        cur.close()

    flash("Cita médica agendada correctamente.", "success")
    return redirect(url_for("crud.pacientes"))


@bp.route("/medicos", methods=["GET", "POST"], strict_slashes=False)
def medicos():
    # Si no hay sesión, primero mostrar formulario de login
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    user_role = session.get("user_role")
    user_id = session.get("user_id")

    # Administrador: se gestiona desde el dashboard /admin
    if user_role == 1:
        flash("No tiene permiso para acceder al módulo Médico", "danger")
        return redirect(url_for("crud.admin", m="medicos"))

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
            consultas_realizadas = []
            recetas = []

            # Consultas realizadas por este médico
            cur.execute(
                "SELECT c.IdConsulta, c.FechaConsulta, c.HI, c.HF, c.Diagnostico, "
                "EXISTS (SELECT 1 FROM recetas r WHERE r.IdConsulta = c.IdConsulta) AS Atendida, "
                "p.Nombre AS NombrePaciente "
                "FROM consultas c "
                "LEFT JOIN pacientes p ON c.IdPaciente = p.IdPaciente "
                "WHERE c.IdMedico=%s ORDER BY c.FechaConsulta DESC",
                (medico_id,),
            )
            consultas = cur.fetchall() or []

            # Consultas realizadas con receta asignada (indicador de consulta realizada)
            cur.execute(
                "SELECT c.IdConsulta, c.FechaConsulta, c.HI, c.HF, c.Diagnostico, "
                "p.Nombre AS NombrePaciente "
                "FROM consultas c "
                "LEFT JOIN pacientes p ON c.IdPaciente = p.IdPaciente "
                "WHERE c.IdMedico=%s "
                "AND EXISTS (SELECT 1 FROM recetas r WHERE r.IdConsulta = c.IdConsulta) "
                "ORDER BY c.FechaConsulta DESC",
                (medico_id,),
            )
            consultas_realizadas = cur.fetchall() or []

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
            consultas_realizadas=consultas_realizadas,
            recetas=recetas,
        )

    flash("No tiene permiso para acceder al módulo Médico", "danger")
    return redirect(url_for("crud.index"))


@bp.route("/medicos/consultas/<int:id_consulta>/atender", methods=["GET", "POST"], strict_slashes=False)
def atender_consulta(id_consulta: int):
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 2:
        flash("No tiene permiso para atender consultas", "danger")
        return redirect(url_for("crud.index"))

    user_id = session.get("user_id")

    with get_connection(current_app) as cn:
        cur = cn.cursor(dictionary=True)

        # Médico vinculado a este usuario
        cur.execute("SELECT IdMedico, Nombre, Foto FROM medicos WHERE IdUsuario=%s", (user_id,))
        medico_row = cur.fetchone()
        if not medico_row:
            cur.close()
            flash("No tiene un registro de médico asociado a este usuario", "danger")
            return redirect(url_for("crud.index"))

        medico_id = medico_row["IdMedico"]

        # Cargar consulta (solo si pertenece al médico)
        cur.execute(
            "SELECT c.IdConsulta, c.FechaConsulta, c.HI, c.HF, c.Diagnostico, "
            "p.Nombre AS NombrePaciente "
            "FROM consultas c "
            "LEFT JOIN pacientes p ON c.IdPaciente = p.IdPaciente "
            "WHERE c.IdConsulta=%s AND c.IdMedico=%s",
            (id_consulta, medico_id),
        )
        consulta_row = cur.fetchone()
        if not consulta_row:
            cur.close()
            flash("Consulta no encontrada o no pertenece a este médico", "danger")
            return redirect(url_for("crud.medicos"))

        # Si ya tiene receta, ya está atendida
        cur.execute("SELECT 1 FROM recetas WHERE IdConsulta=%s LIMIT 1", (id_consulta,))
        if cur.fetchone():
            cur.close()
            flash("Esta consulta ya fue atendida (ya tiene receta asignada)", "warning")
            return redirect(url_for("crud.medicos"))

        # Medicamentos para la receta
        cur.execute("SELECT IdMedicamento, Nombre FROM medicamentos ORDER BY Nombre")
        medicamentos = cur.fetchall() or []

        if request.method == "POST":
            diagnostico = (request.form.get("Diagnostico") or "").strip()
            id_medicamento = (request.form.get("IdMedicamento") or "").strip()
            cantidad_s = (request.form.get("Cantidad") or "").strip()

            errors: list[str] = []
            if not diagnostico:
                errors.append("Debe ingresar el diagnóstico")
            if not id_medicamento:
                errors.append("Debe seleccionar un medicamento")
            try:
                cantidad = int(cantidad_s)
                if cantidad <= 0:
                    raise ValueError()
            except Exception:
                errors.append("La cantidad debe ser un número mayor a 0")

            if errors:
                for e in errors:
                    flash(e, "danger")
            else:
                # Asegurar nuevamente que no se atendió (carrera)
                cur.execute("SELECT 1 FROM recetas WHERE IdConsulta=%s LIMIT 1", (id_consulta,))
                if cur.fetchone():
                    cur.close()
                    flash("Esta consulta ya fue atendida por otro proceso", "warning")
                    return redirect(url_for("crud.medicos"))

                cur.execute(
                    "UPDATE consultas SET Diagnostico=%s WHERE IdConsulta=%s AND IdMedico=%s",
                    (diagnostico, id_consulta, medico_id),
                )
                cur.execute(
                    "INSERT INTO recetas(IdConsulta, IdMedicamento, Cantidad) VALUES(%s,%s,%s)",
                    (id_consulta, int(id_medicamento), cantidad),
                )
                cn.commit()
                cur.close()
                flash("Consulta atendida: diagnóstico actualizado y receta asignada", "success")
                return redirect(url_for("crud.medicos"))

        cur.close()

    return render_template(
        "atender_consulta.html",
        consulta=consulta_row,
        medicamentos=medicamentos,
        nav_nombre=(session.get("user_name") or ""),
        nav_foto=(medico_row.get("Foto") or ""),
    )


@bp.get("/medicos/consultas/<int:id_consulta>/siguiente-cita")
def siguiente_cita(id_consulta: int):
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 2:
        flash("No tiene permiso para agendar citas", "danger")
        return redirect(url_for("crud.index"))

    today = date.today()

    # Parámetros de navegación
    mes = _parse_int(request.args.get("mes"), today.month)
    anio = _parse_int(request.args.get("anio"), today.year)

    if (anio, mes) < (today.year, today.month):
        anio, mes = today.year, today.month
    if (anio, mes) > (_MAX_AGENDAR_FECHA.year, _MAX_AGENDAR_FECHA.month):
        anio, mes = _MAX_AGENDAR_FECHA.year, _MAX_AGENDAR_FECHA.month

    fecha_sel = (request.args.get("fecha") or "").strip()
    if fecha_sel:
        try:
            fecha_obj = datetime.strptime(fecha_sel, "%Y-%m-%d").date()
            if fecha_obj < today or fecha_obj > _MAX_AGENDAR_FECHA:
                fecha_sel = ""
        except Exception:
            fecha_sel = ""

    user_id = int(session.get("user_id"))

    with get_connection(current_app) as cn:
        cur = cn.cursor(dictionary=True)

        # Médico
        cur.execute(
            "SELECT m.IdMedico, m.Nombre, m.Foto, m.Especialidad, e.IdEsp, e.Descripcion, e.Dias, e.Franja_HI, e.Franja_HF "
            "FROM medicos m LEFT JOIN especialidades e ON m.Especialidad = e.IdEsp "
            "WHERE m.IdUsuario=%s",
            (user_id,),
        )
        medico_row = cur.fetchone()
        if not medico_row:
            cur.close()
            flash("No tiene un registro de médico asociado a este usuario", "danger")
            return redirect(url_for("crud.index"))

        medico_id = int(medico_row["IdMedico"])
        id_especialidad = str(medico_row.get("IdEsp") or medico_row.get("Especialidad") or "").strip()
        id_medico = str(medico_id)

        # Consulta original (debe pertenecer al médico)
        cur.execute(
            "SELECT c.IdConsulta, c.IdPaciente, p.Nombre AS NombrePaciente "
            "FROM consultas c LEFT JOIN pacientes p ON c.IdPaciente = p.IdPaciente "
            "WHERE c.IdConsulta=%s AND c.IdMedico=%s",
            (id_consulta, medico_id),
        )
        consulta_row = cur.fetchone()
        if not consulta_row:
            cur.close()
            flash("Consulta no encontrada o no pertenece a este médico", "danger")
            return redirect(url_for("crud.medicos"))

        # Solo permitir siguiente cita si la consulta ya fue atendida (tiene receta)
        cur.execute("SELECT 1 FROM recetas WHERE IdConsulta=%s LIMIT 1", (id_consulta,))
        if not cur.fetchone():
            cur.close()
            flash("La consulta aún no está atendida (no tiene receta)", "warning")
            return redirect(url_for("crud.medicos"))

        paciente_id = int(consulta_row["IdPaciente"])

        # Reutilizar el mismo UI de agendar_cita.html, pero con especialidad/médico fijos
        especialidades = [
            {
                "IdEsp": medico_row.get("IdEsp") or medico_row.get("Especialidad"),
                "Descripcion": medico_row.get("Descripcion") or medico_row.get("NombreEspecialidad") or "",
                "Dias": medico_row.get("Dias"),
                "Franja_HI": medico_row.get("Franja_HI"),
                "Franja_HF": medico_row.get("Franja_HF"),
            }
        ]
        medicos = [{"IdMedico": medico_id, "Nombre": medico_row.get("Nombre") or ""}]

        dias_con_horarios: dict[str, int] = {}
        horarios: list[str] = []

        dias_permitidos = _dias_str_to_weekdays(str(medico_row.get("Dias") or ""))
        franja_hi = medico_row.get("Franja_HI")
        franja_hf = medico_row.get("Franja_HF")

        _, days_in_month = pycalendar.monthrange(anio, mes)
        for day in range(1, days_in_month + 1):
            d = date(anio, mes, day)
            if d < today or d > _MAX_AGENDAR_FECHA:
                continue
            if dias_permitidos and d.weekday() not in dias_permitidos:
                continue
            iso = d.isoformat()
            slots = _get_available_slots_30m(cn, medico_id, iso, franja_hi, franja_hf)
            if d == today:
                now = datetime.now()
                now_min = now.hour * 60 + now.minute
                slots = [s for s in slots if _time_to_minutes(s) > now_min]
            if slots:
                dias_con_horarios[iso] = len(slots)

        if fecha_sel:
            try:
                dsel = datetime.strptime(fecha_sel, "%Y-%m-%d").date()
            except Exception:
                dsel = None

            if dsel and (not dias_permitidos or dsel.weekday() in dias_permitidos) and dsel >= today:
                horarios = _get_available_slots_30m(cn, medico_id, fecha_sel, franja_hi, franja_hf)
                if dsel == today:
                    now = datetime.now()
                    now_min = now.hour * 60 + now.minute
                    horarios = [s for s in horarios if _time_to_minutes(s) > now_min]
            else:
                fecha_sel = ""

        cur.close()

    calendario = _build_calendar(anio, mes, today, fecha_sel or None, dias_con_horarios)
    nombre_mes = f"{_month_name_es(mes)} {anio}"

    es_primer_mes = (anio, mes) == (today.year, today.month)
    es_ultimo_mes = (anio, mes) == (_MAX_AGENDAR_FECHA.year, _MAX_AGENDAR_FECHA.month)

    return render_template(
        "agendar_cita.html",
        especialidades=especialidades,
        medicos=medicos,
        id_especialidad=id_especialidad,
        id_medico=id_medico,
        mes=mes,
        anio=anio,
        fecha=fecha_sel,
        calendario=calendario,
        dias_con_horarios=dias_con_horarios,
        horarios=horarios,
        nombre_mes=nombre_mes,
        es_primer_mes=es_primer_mes,
        es_ultimo_mes=es_ultimo_mes,
        agendar_get_action=url_for("crud.siguiente_cita", id_consulta=id_consulta),
        agendar_post_action=url_for("crud.siguiente_cita_confirmar", id_consulta=id_consulta),
        volver_url=url_for("crud.medicos"),
        extra_get_params={"idConsulta": str(id_consulta)},
        extra_post_params={"IdPaciente": str(paciente_id)},
        nav_nombre=(session.get("user_name") or ""),
        nav_foto=(medico_row.get("Foto") or ""),
    )


@bp.post("/medicos/consultas/<int:id_consulta>/siguiente-cita/confirmar")
def siguiente_cita_confirmar(id_consulta: int):
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 2:
        flash("No tiene permiso para agendar citas", "danger")
        return redirect(url_for("crud.index"))

    id_especialidad = (request.form.get("IdEspecialidad") or "").strip()
    id_medico = (request.form.get("IdMedico") or "").strip()
    fecha = (request.form.get("FechaConsulta") or "").strip()
    hi = (request.form.get("HI") or "").strip()
    id_paciente = (request.form.get("IdPaciente") or "").strip()

    if not (id_especialidad and id_medico and fecha and hi and id_paciente):
        flash("Complete especialidad, médico, fecha y horario.", "warning")
        return redirect(url_for("crud.siguiente_cita", id_consulta=id_consulta))

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except Exception:
        flash("Fecha inválida.", "warning")
        return redirect(url_for("crud.siguiente_cita", id_consulta=id_consulta))

    if fecha_obj < date.today() or fecha_obj > _MAX_AGENDAR_FECHA:
        flash("La fecha seleccionada no está permitida.", "warning")
        return redirect(url_for("crud.siguiente_cita", id_consulta=id_consulta))

    # HF = HI + 30 min
    try:
        hi_min = _time_to_minutes(hi)
        hf_min = hi_min + 30
        hf = _minutes_to_hhmm(hf_min) + ":00"
        hi_db = hi + ":00" if len(hi) == 5 else hi
    except Exception:
        flash("Horario inválido.", "warning")
        return redirect(url_for("crud.siguiente_cita", id_consulta=id_consulta))

    user_id = int(session.get("user_id"))

    with get_connection(current_app) as cn:
        cur = cn.cursor(dictionary=True)

        # Médico del usuario (evitar que agende con otro médico)
        cur.execute("SELECT IdMedico, Especialidad FROM medicos WHERE IdUsuario=%s", (user_id,))
        medico_row = cur.fetchone()
        if not medico_row:
            cur.close()
            flash("No tiene un registro de médico asociado a este usuario.", "danger")
            return redirect(url_for("crud.medicos"))

        if str(medico_row.get("IdMedico")) != str(id_medico):
            cur.close()
            flash("Médico inválido.", "danger")
            return redirect(url_for("crud.medicos"))

        # Consulta original y paciente (evitar manipulación de IdPaciente)
        cur.execute(
            "SELECT c.IdPaciente FROM consultas c WHERE c.IdConsulta=%s AND c.IdMedico=%s",
            (id_consulta, medico_row["IdMedico"]),
        )
        consulta_row = cur.fetchone()
        if not consulta_row:
            cur.close()
            flash("Consulta no encontrada o no pertenece a este médico", "danger")
            return redirect(url_for("crud.medicos"))

        if str(consulta_row.get("IdPaciente")) != str(id_paciente):
            cur.close()
            flash("Paciente inválido.", "danger")
            return redirect(url_for("crud.medicos"))

        # Validar que la consulta original está atendida
        cur.execute("SELECT 1 FROM recetas WHERE IdConsulta=%s LIMIT 1", (id_consulta,))
        if not cur.fetchone():
            cur.close()
            flash("La consulta aún no está atendida.", "warning")
            return redirect(url_for("crud.medicos"))

        # Validar médico vs especialidad y obtener franja/días
        cur.execute(
            "SELECT m.IdMedico, e.Dias, e.Franja_HI, e.Franja_HF "
            "FROM medicos m LEFT JOIN especialidades e ON m.Especialidad = e.IdEsp "
            "WHERE m.IdMedico=%s AND m.Especialidad=%s",
            (id_medico, id_especialidad),
        )
        medico_especialidad_row = cur.fetchone()
        if not medico_especialidad_row:
            cur.close()
            flash("El médico no corresponde a la especialidad.", "warning")
            return redirect(url_for("crud.siguiente_cita", id_consulta=id_consulta))

        dias_permitidos = _dias_str_to_weekdays(str(medico_especialidad_row.get("Dias") or ""))
        if dias_permitidos and fecha_obj.weekday() not in dias_permitidos:
            cur.close()
            flash("La especialidad no atiende en el día seleccionado.", "warning")
            return redirect(url_for("crud.siguiente_cita", id_consulta=id_consulta, fecha=fecha))

        franja_hi = medico_especialidad_row.get("Franja_HI")
        franja_hf = medico_especialidad_row.get("Franja_HF")
        slots = _get_available_slots_30m(cn, int(id_medico), fecha, franja_hi, franja_hf)
        if hi not in slots:
            cur.close()
            flash("El horario seleccionado ya no está disponible.", "warning")
            return redirect(url_for("crud.siguiente_cita", id_consulta=id_consulta, fecha=fecha))

        # Validar choque
        cur.execute(
            "SELECT 1 FROM consultas "
            "WHERE IdMedico=%s AND FechaConsulta=%s "
            "AND NOT (HF <= %s OR HI >= %s) LIMIT 1",
            (id_medico, fecha, hi_db, hf),
        )
        if cur.fetchone():
            cur.close()
            flash("Ese horario acaba de ocuparse. Seleccione otro.", "warning")
            return redirect(url_for("crud.siguiente_cita", id_consulta=id_consulta, fecha=fecha))

        # Validar choque del paciente (no puede tener dos citas en el mismo horario)
        cur.execute(
            "SELECT 1 FROM consultas "
            "WHERE IdPaciente=%s AND FechaConsulta=%s "
            "AND NOT (HF <= %s OR HI >= %s) LIMIT 1",
            (int(id_paciente), fecha, hi_db, hf),
        )
        if cur.fetchone():
            cur.close()
            flash("El paciente ya tiene una cita agendada en esa fecha y hora.", "warning")
            return redirect(url_for("crud.siguiente_cita", id_consulta=id_consulta, fecha=fecha, conflict=1))

        # Insertar nueva consulta (siguiente cita)
        cur.execute(
            "INSERT INTO consultas(IdMedico, IdPaciente, FechaConsulta, HI, HF, Diagnostico) "
            "VALUES(%s,%s,%s,%s,%s,%s)",
            (id_medico, int(id_paciente), fecha, hi_db, hf, "Pendiente"),
        )
        cn.commit()
        cur.close()

    flash("Siguiente cita agendada correctamente.", "success")
    return redirect(url_for("crud.medicos"))


@bp.route("/especialidades", methods=["GET", "POST"], strict_slashes=False)
def especialidades():
    # Solo administradores
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 1:
        flash("No tiene permiso para acceder al módulo Especialidades", "danger")
        return redirect(url_for("crud.index"))

    return redirect(url_for("crud.admin", m="especialidades"))


@bp.route("/medicamentos", methods=["GET", "POST"], strict_slashes=False)
def medicamentos():
    # Solo administradores
    if "user_id" not in session:
        return redirect(url_for("crud.login", next=request.path))

    if session.get("user_role") != 1:
        flash("No tiene permiso para acceder al módulo Medicamentos", "danger")
        return redirect(url_for("crud.index"))

    return redirect(url_for("crud.admin", m="medicamentos"))


@bp.route("/consultas", methods=["GET", "POST"], strict_slashes=False)
def consultas():
    return _handle_model(Consulta)


@bp.route("/recetas", methods=["GET", "POST"], strict_slashes=False)
def recetas():
    return _handle_model(Receta)
