from __future__ import annotations

import base64
import html
from typing import Any, Dict, List, Tuple


class Usuario:
    """CRUD POO para la tabla `usuarios`.

    Tabla: usuarios(IdUsuario, Nombre, Password, Rol)
    """

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

        # SQL propio
        self.sql_list = "SELECT IdUsuario, Nombre, Rol FROM usuarios ORDER BY IdUsuario DESC"
        self.sql_detail = "SELECT IdUsuario, Nombre, Password, Rol FROM usuarios WHERE IdUsuario=%s"
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
        items = (
            '<li class="nav-item"><a class="nav-link" href="/pacientes">'
            '<i class="bi bi-people-fill me-1"></i>Pacientes</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/medicos">'
            '<i class="bi bi-person-badge-fill me-1"></i>Médicos</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/especialidades">'
            '<i class="bi bi-heart-pulse me-1"></i>Especialidades</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/medicamentos">'
            '<i class="bi bi-capsule me-1"></i>Medicamentos</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/consultas">'
            '<i class="bi bi-clipboard2-pulse me-1"></i>Consultas</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/recetas">'
            '<i class="bi bi-receipt me-1"></i>Recetas</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/roles">'
            '<i class="bi bi-shield-lock-fill me-1"></i>Roles</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/usuarios">'
            '<i class="bi bi-person-lines-fill me-1"></i>Usuarios</a></li>'
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
            '<div class="d-flex flex-wrap justify-content-center justify-content-lg-end mt-2 mt-lg-0">'
            '<a href="/login" class="btn btn-primary btn-sm me-3">'
            '<i class="bi bi-person-fill me-1"></i> Iniciar sesión'
            "</a>"
            '<a href="/register" class="btn btn-outline-primary btn-sm">'
            '<i class="bi bi-person-plus-fill me-1"></i> Registrarse'
            "</a>"
            "</div>"
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

    # ----------------------------- CRUD methods --------------------------------
    def get_list(self) -> str:
        cur = self.cn.cursor(dictionary=True)
        cur.execute(self.sql_list)
        rows: List[Dict[str, Any]] = cur.fetchall() or []
        cur.close()

        d_new = self._d_encode("new", 0)
        header = "".join(
            f"<th>{h}</th>" for h in ["IdUsuario", "Nombre", "Rol", "Acciones"]
        )
        body = ""
        for r in rows:
            pk = int(r["IdUsuario"])
            d_act = self._d_encode("act", pk)
            d_det = self._d_encode("det", pk)
            d_del = self._d_encode("del", pk)
            body += (
                "<tr>"
                f"<td>{pk}</td>"
                f"<td>{html.escape(str(r.get('Nombre','')))}</td>"
                f"<td>{html.escape(str(r.get('Rol','')))}</td>"
                "<td>"
                f"<a class='btn btn-sm btn-primary me-1' href='{self.path}?d={d_act}'>Editar</a>"
                f"<a class='btn btn-sm btn-outline-secondary me-1' href='{self.path}?d={d_det}'>Detalle</a>"
                f"<a class='btn btn-sm btn-danger' href='{self.path}?d={d_del}' onclick=\"return confirm('¿Eliminar este registro?');\">Eliminar</a>"
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
        disabled_pk = (not is_new)

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
        form += self._input("IdUsuario", "IdUsuario", values["IdUsuario"], disabled_pk, "number")
        form += self._input("Nombre", "Nombre", values["Nombre"], False)
        form += self._input("Password", "Password", values["Password"], False, "password")
        form += self._input("Rol", "Rol", values["Rol"], False)

        title = "Nuevo Usuario" if is_new else f"Actualizar Usuario #{id}"
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
        form += self._input("IdUsuario", "IdUsuario", str(row.get("IdUsuario", "")), True, "number")
        form += self._input("Nombre", "Nombre", str(row.get("Nombre", "")), True)
        form += self._input("Password", "Password", str(row.get("Password", "")), True, "password")
        form += self._input("Rol", "Rol", str(row.get("Rol", "")), True)

        return (
            f"<h2 class='mb-3'>Detalle Usuario #{id}</h2>"
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
            cur = self.cn.cursor()
            cur.execute(self.sql_delete, (id,))
            self.cn.commit()
            cur.close()
            return self._msg_success("Usuario eliminado correctamente")
        except Exception as ex:
            return self._msg_error(f"Error SQL: {ex}")
