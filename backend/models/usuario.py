from __future__ import annotations

import base64
import html
from typing import Any, Dict, List, Tuple


class Usuario:

    table_name = "usuarios"
    pk = "IdUsuario"
    title = "Usuarios"
    path = "/usuarios"

    def __init__(self, cn):
        self.cn = cn

        # Columnas principales (respetan nombres de BD)
        self.IdUsuario: int | None = None
        self.Nombre: str = ""
        self.Password: str = ""
        self.Rol: str = ""

        # SQL propio (JOIN para mostrar el nombre del rol)
        self.sql_list = (
            "SELECT u.IdUsuario, u.Nombre, u.Rol, r.Nombre AS NombreRol "
            "FROM usuarios u "
            "LEFT JOIN roles r ON u.Rol = r.IdRol "
            "ORDER BY u.IdUsuario DESC"
        )
        self.sql_detail = (
            "SELECT u.IdUsuario, u.Nombre, u.Password, u.Rol, r.Nombre AS NombreRol "
            "FROM usuarios u "
            "LEFT JOIN roles r ON u.Rol = r.IdRol "
            "WHERE u.IdUsuario=%s"
        )
        self.sql_insert = "INSERT INTO usuarios(Nombre, Password, Rol) VALUES(%s,%s,%s)"
        self.sql_update = "UPDATE usuarios SET Nombre=%s, Password=%s, Rol=%s WHERE IdUsuario=%s"
        self.sql_delete = "DELETE FROM usuarios WHERE IdUsuario=%s"

    # ----------------------------- Base64 d helpers -----------------------------
    def _d_encode(self, op: str, id_: int) -> str:
        raw = f"{op}/{id_}".encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8")

    def _d_decode(self, d: str) -> Tuple[str, int]:
        raw = base64.urlsafe_b64decode(d.encode("utf-8")).decode("utf-8")
        op, id_s = raw.split("/", 1)
        return op, int(id_s)

    # ----------------------------- UI helpers ----------------------------------
    def navbar(self) -> str:
        # Navbar del módulo Administrador: muestra todas las tablas principales
        # (excepto Consultas y Recetas, que no son gestionadas aquí).
        items = (
            '<li class="nav-item"><a class="nav-link" href="/usuarios">'
            '<i class="bi bi-shield-lock-fill me-1"></i>Usuarios</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/roles">'
            '<i class="bi bi-key-fill me-1"></i>Roles</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/pacientes">'
            '<i class="bi bi-people-fill me-1"></i>Pacientes</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/medicos">'
            '<i class="bi bi-person-badge-fill me-1"></i>Médicos</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/especialidades">'
            '<i class="bi bi-card-list me-1"></i>Especialidades</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/medicamentos">'
            '<i class="bi bi-capsule-pill me-1"></i>Medicamentos</a></li>'
        )
        return (
            '<nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm py-2">'
            '<div class="container-fluid px-4">'
            '<a class="navbar-brand d-flex flex-column align-items-start" href="/">'
            '<img src="/static/img/logo.png" alt="Logo Veris" class="img-fluid mb-1" '
            'style="height: 35px; width: auto;">'
            "<span class='slogan'>Hacemos <strong>fácil cuidarte</strong></span>"
            "</a>"
            '<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#menuPrincipal"'
            ' aria-controls="menuPrincipal" aria-expanded="false" aria-label="Alternar navegación">'
            '<span class="navbar-toggler-icon"></span></button>'
            '<div class="collapse navbar-collapse justify-content-between" id="menuPrincipal">'
            '<ul class="navbar-nav flex-grow-1 justify-content-evenly text-center">'
            f"{items}"
            "</ul>"
            "</div></div></nav>"
        )

    def _msg_success(self, text: str) -> str:
        return f'<div class="alert alert-success" role="alert">{html.escape(text)}</div>'

    def _msg_error(self, text: str) -> str:
        return f'<div class="alert alert-danger" role="alert">{html.escape(text)}</div>'

    def _input(self, name: str, label: str, value: str, disabled: bool, type_: str = "text") -> str:
        dis = " disabled" if disabled else ""
        return (
            '<div class="mb-3">'
            f'<label class="form-label" for="{html.escape(name)}">{html.escape(label)}</label>'
            f'<input class="form-control" id="{html.escape(name)}" name="{html.escape(name)}" '
            f'type="{html.escape(type_)}" value="{html.escape(value)}"{dis} />'
            "</div>"
        )

    def _select(self, name: str, label: str, options: List[Dict[str, Any]], selected: str, disabled: bool) -> str:
        dis = " disabled" if disabled else ""
        out = '<div class="mb-3">'
        out += f'<label class="form-label" for="{html.escape(name)}">{html.escape(label)}</label>'
        out += f'<select class="form-select" id="{html.escape(name)}" name="{html.escape(name)}"{dis}>'
        out += "<option value=''>Seleccione...</option>"
        for opt in options:
            vid = str(opt.get("IdRol", ""))
            vname = str(opt.get("Nombre", ""))
            sel = " selected" if vid and vid == (selected or "") else ""
            out += f"<option value='{html.escape(vid)}'{sel}>{html.escape(vname)}</option>"
        out += "</select></div>"
        return out

    def _get_roles_medico_paciente(self) -> List[Dict[str, Any]]:
        """Retorna roles para asignación de usuarios (solo Médico=2 y Paciente=3)."""

        cur = self.cn.cursor(dictionary=True)
        cur.execute(
            "SELECT IdRol, Nombre FROM roles WHERE IdRol IN (2,3) ORDER BY IdRol"
        )
        rows: List[Dict[str, Any]] = cur.fetchall() or []
        cur.close()
        return rows

    # ----------------------------- CRUD methods --------------------------------
    def get_list(self) -> str:
        cur = self.cn.cursor(dictionary=True)
        cur.execute(self.sql_list)
        rows: List[Dict[str, Any]] = cur.fetchall() or []
        cur.close()

        d_new = self._d_encode("new", 0)
        header = "".join(
            f"<th>{h}</th>" for h in ["Nombre", "Rol", "Acciones"]
        )
        body = ""
        for r in rows:
            pk = int(r["IdUsuario"])
            d_act = self._d_encode("act", pk)
            d_det = self._d_encode("det", pk)
            d_del = self._d_encode("del", pk)
            body += (
                "<tr>"
                f"<td>{html.escape(str(r.get('Nombre','')))}</td>"
                f"<td>{html.escape(str(r.get('NombreRol','')))}</td>"
                "<td>"
                f"<a class='btn btn-sm btn-primary me-1' href='{self.path}?d={d_act}'>Editar</a>"
                f"<a class='btn btn-sm btn-outline-secondary me-1' href='{self.path}?d={d_det}'>Detalle</a>"
                f"<a class='btn btn-sm btn-danger' href='{self.path}?d={d_del}' data-veris-confirm='¿Eliminar este registro?'>Eliminar</a>"
                "</td>"
                "</tr>"
            )

        return (
            "<main class='container my-4 veris-tabla-container'>"
            f"<h2 class='veris-tabla-title'>{html.escape(self.title)}</h2>"
            f"<p class='veris-tabla-actions'><a class='btn veris-tabla-btn-crear' href='{self.path}?d={d_new}'>Crear nuevo</a></p>"
            "<div class='veris-tabla-wrapper'>"
            "<table class='table veris-tabla table-bordered table-striped'>"
            f"<thead class='veris-tabla-thead'><tr>{header}</tr></thead>"
            f"<tbody class='veris-tabla-body-content'>{body}</tbody>"
            "</table>"
            "</div>"
            "</main>"
        )

    def get_form(self, id: int = 0) -> str:
        is_new = id == 0
        op = "new" if is_new else "act"
        values = {"IdUsuario": "", "Nombre": "", "Password": "", "Rol": ""}
        if not is_new:
            cur = self.cn.cursor(dictionary=True)
            cur.execute(self.sql_detail, (id,))
            row = cur.fetchone()
            cur.close()
            if not row:
                return self._msg_error("Registro no encontrado")
            values = {
                "IdUsuario": str(row.get("IdUsuario", "")),
                "Nombre": str(row.get("Nombre", "")),
                "Password": str(row.get("Password", "")),
                "Rol": str(row.get("Rol", "")),
            }

        d = self._d_encode(op, id)
        form = ""
        # No mostrar IdUsuario en el formulario (se maneja internamente con d)
        form += self._input("Nombre", "Nombre", values["Nombre"], False)
        form += self._input("Password", "Password", values["Password"], False, "password")

        roles = self._get_roles_medico_paciente()
        form += self._select("Rol", "Rol", roles, values["Rol"], False)

        title = "Nuevo Usuario" if is_new else f"Actualizar Usuario"
        return (
            f"<h2 class='mb-3'>{html.escape(title)}</h2>"
            f"<form method='post'>"
            f"<input type='hidden' name='d' value='{html.escape(d)}' />"
            f"{form}"
            "<button class='btn btn-primary' type='submit'>Guardar</button> "
            f"<a class='btn btn-outline-secondary' href='{self.path}'>Volver</a>"
            "</form>"
        )

    def get_detail(self, id: int) -> str:
        cur = self.cn.cursor(dictionary=True)
        cur.execute(self.sql_detail, (id,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return self._msg_error("Registro no encontrado")

        form = ""
        # No mostrar IdUsuario en detalle
        form += self._input("Nombre", "Nombre", str(row.get("Nombre", "")), True)
        form += self._input("Password", "Password", str(row.get("Password", "")), True, "password")
        form += self._input("Rol", "Rol", str(row.get("NombreRol", "")), True)

        return (
            f"<h2 class='mb-3'>Detalle Usuario</h2>"
            f"<form>"
            f"{form}"
            f"<a class='btn btn-outline-secondary' href='{self.path}'>Volver</a>"
            "</form>"
        )

    def save(self, form_data) -> str:
        d = form_data.get("d", "")
        try:
            op, id_ = self._d_decode(d)
        except Exception:
            return self._msg_error("Parámetro d inválido")

        nombre = (form_data.get("Nombre") or "").strip()
        password = (form_data.get("Password") or "").strip()
        rol = (form_data.get("Rol") or "").strip()

        if not nombre:
            return self._msg_error("El nombre de usuario es obligatorio")
        if not password:
            return self._msg_error("La contraseña es obligatoria")

        if rol not in ("2", "3"):
            return self._msg_error("Rol inválido: seleccione Médico o Paciente")

        # Validar usuario único (case-insensitive) antes de insertar/actualizar
        curv = self.cn.cursor(dictionary=True)
        if op == "new":
            curv.execute(
                "SELECT 1 FROM usuarios WHERE LOWER(Nombre)=LOWER(%s) LIMIT 1",
                (nombre,),
            )
        else:
            curv.execute(
                "SELECT 1 FROM usuarios WHERE LOWER(Nombre)=LOWER(%s) AND IdUsuario<>%s LIMIT 1",
                (nombre, id_),
            )
        exists = curv.fetchone()
        curv.close()
        if exists:
            return self._msg_error("Ese nombre de usuario ya está registrado")

        try:
            cur = self.cn.cursor()
            if op == "new":
                cur.execute(self.sql_insert, (nombre, password, rol))
                self.cn.commit()
                cur.close()
                return self._msg_success("Usuario creado correctamente")

            if op == "act":
                cur.execute(self.sql_update, (nombre, password, rol, id_))
                self.cn.commit()
                cur.close()
                return self._msg_success("Usuario actualizado correctamente")

            cur.close()
            return self._msg_error("Operación no permitida")
        except Exception as ex:
            return self._msg_error(f"Error SQL: {ex}")

    def delete(self, id: int) -> str:
        try:
            # No permitir eliminar si está asociado a médico o paciente
            curv = self.cn.cursor(dictionary=True)
            curv.execute("SELECT 1 FROM medicos WHERE IdUsuario=%s LIMIT 1", (id,))
            if curv.fetchone():
                curv.close()
                return self._msg_error("No se puede eliminar el usuario porque está asociado a un médico")
            curv.execute("SELECT 1 FROM pacientes WHERE IdUsuario=%s LIMIT 1", (id,))
            if curv.fetchone():
                curv.close()
                return self._msg_error("No se puede eliminar el usuario porque está asociado a un paciente")
            curv.close()

            cur = self.cn.cursor()
            cur.execute(self.sql_delete, (id,))
            self.cn.commit()
            cur.close()
            return self._msg_success("Usuario eliminado correctamente")
        except Exception as ex:
            return self._msg_error(f"Error SQL: {ex}")
