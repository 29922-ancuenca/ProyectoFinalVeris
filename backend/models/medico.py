from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Any, Dict, List, Tuple

from flask import current_app, request
from werkzeug.utils import secure_filename


class Medico:
    """CRUD POO para la tabla `medicos`.

    Tabla: medicos(IdMedico, Nombre, Especialidad, IdUsuario, Foto)
    """

    table_name = "medicos"
    pk = "IdMedico"
    title = "Médicos"
    path = "/medicos"

    def __init__(self, cn):
        self.cn = cn

        self.IdMedico: int | None = None
        self.Nombre: str = ""
        self.Especialidad: str = ""
        self.IdUsuario: int | None = None
        self.Foto: str = ""

        # JOIN para mostrar el nombre de la especialidad en lugar del id
        self.sql_list = (
            "SELECT m.IdMedico, m.Nombre, e.Descripcion AS Especialidad, m.IdUsuario, m.Foto "
            "FROM medicos m "
            "LEFT JOIN especialidades e ON m.Especialidad = e.IdEsp "
            "ORDER BY m.IdMedico DESC"
        )
        self.sql_detail = (
            "SELECT m.IdMedico, m.Nombre, m.Especialidad AS IdEsp, "
            "e.Descripcion AS Especialidad, m.IdUsuario, m.Foto "
            "FROM medicos m "
            "LEFT JOIN especialidades e ON m.Especialidad = e.IdEsp "
            "WHERE m.IdMedico=%s"
        )
        self.sql_insert = "INSERT INTO medicos(Nombre, Especialidad, IdUsuario, Foto) VALUES(%s,%s,%s,%s)"
        self.sql_update = "UPDATE medicos SET Nombre=%s, Especialidad=%s, IdUsuario=%s, Foto=%s WHERE IdMedico=%s"
        self.sql_delete = "DELETE FROM medicos WHERE IdMedico=%s"

    def _d_encode(self, op: str, id_: int) -> str:
        raw = f"{op}/{id_}".encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8")

    def _d_decode(self, d: str) -> Tuple[str, int]:
        raw = base64.urlsafe_b64decode(d.encode("utf-8")).decode("utf-8")
        op, id_s = raw.split("/", 1)
        return op, int(id_s)

    def navbar(self) -> str:
        items = (
            '<li class="nav-item"><a class="nav-link" href="/pacientes">'
            '<i class="bi bi-people-fill me-1"></i>Módulo Paciente</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/medicos">'
            '<i class="bi bi-person-badge-fill me-1"></i>Módulo Médico</a></li>'
            '<li class="nav-item"><a class="nav-link" href="/usuarios">'
            '<i class="bi bi-shield-lock-fill me-1"></i>Módulo Administrador</a></li>'
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

    def get_list(self) -> str:
        cur = self.cn.cursor(dictionary=True)
        cur.execute(self.sql_list)
        rows: List[Dict[str, Any]] = cur.fetchall() or []
        cur.close()

        d_new = self._d_encode("new", 0)
        headers = ["Nombre", "Especialidad", "Foto", "Acciones"]
        thead = "".join(f"<th>{h}</th>" for h in headers)

        tbody = ""
        for r in rows:
            pk = int(r["IdMedico"])
            d_act = self._d_encode("act", pk)
            d_det = self._d_encode("det", pk)
            d_del = self._d_encode("del", pk)

            foto = str(r.get("Foto") or "")
            foto_html = ""
            if foto:
                foto_html = (
                    f"<div><img src='/static/img/usuarios/{html.escape(foto)}' width='50' onerror=\"this.style.display='none'\" /></div>"
                    f"<small class='text-muted'>{html.escape(foto)}</small>"
                )

            tbody += (
                "<tr>"
                f"<td>{html.escape(str(r.get('Nombre','')))}</td>"
                f"<td>{html.escape(str(r.get('Especialidad','')))}</td>"
                f"<td>{foto_html}</td>"
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
            f"<thead class='veris-tabla-thead'><tr>{thead}</tr></thead>"
            f"<tbody class='veris-tabla-body-content'>{tbody}</tbody>"
            "</table>"
            "</div>"
            "</main>"
        )

    def get_form(self, id: int = 0) -> str:
        is_new = id == 0
        op = "new" if is_new else "act"
        values = {"IdMedico": "", "Nombre": "", "Especialidad": "", "IdUsuario": "", "Foto": ""}
        if not is_new:
            cur = self.cn.cursor(dictionary=True)
            cur.execute(self.sql_detail, (id,))
            row = cur.fetchone()
            cur.close()
            if not row:
                return self._msg_error("Registro no encontrado")
            values["IdMedico"] = "" if row.get("IdMedico") is None else str(row.get("IdMedico"))
            values["Nombre"] = "" if row.get("Nombre") is None else str(row.get("Nombre"))
            # Guardamos el id de especialidad (IdEsp) para el select
            values["Especialidad"] = "" if row.get("IdEsp") is None else str(row.get("IdEsp"))
            values["IdUsuario"] = "" if row.get("IdUsuario") is None else str(row.get("IdUsuario"))
            values["Foto"] = "" if row.get("Foto") is None else str(row.get("Foto"))

        # Cargar especialidades para el select (mostrar nombre, guardar id)
        cur = self.cn.cursor(dictionary=True)
        cur.execute("SELECT IdEsp, Descripcion FROM especialidades ORDER BY Descripcion")
        especialidades: List[Dict[str, Any]] = cur.fetchall() or []
        cur.close()

        d = self._d_encode(op, id)
        form = ""
        # No mostrar IdMedico ni IdUsuario en el formulario (se manejan internamente)
        if values["IdUsuario"]:
            form += (
                f"<input type='hidden' name='IdUsuario' value='{html.escape(values['IdUsuario'])}' />"
            )
        form += self._input("Nombre", "Nombre", values["Nombre"], False)
        # Selector de especialidad por nombre (value = id)
        form += "<div class='mb-3'>"
        form += "<label class='form-label' for='Especialidad'>Especialidad</label>"
        form += "<select class='form-select' id='Especialidad' name='Especialidad'>"
        for e in especialidades:
            eid = str(e.get("IdEsp", ""))
            selected = " selected" if eid == values["Especialidad"] else ""
            form += (
                f"<option value='{html.escape(eid)}'{selected}>"
                f"{html.escape(str(e.get('Descripcion', '')))}"
                "</option>"
            )
        form += "</select></div>"

        # Campo para subir nueva foto (input file en lugar del nombre)
        if values["Foto"]:
            form += (
                "<div class='mb-3'>"
                "<label class='form-label'>Foto actual</label>"
                f"<div><img src='/static/img/usuarios/{html.escape(values['Foto'])}' "
                "class='img-thumbnail' style='max-width: 100px;' "
                "onerror=\"this.style.display='none'\" /></div>"
                "</div>"
            )

        form += (
            "<div class='mb-3'>"
            "<label class='form-label' for='Foto'>Nueva foto</label>"
            "<input class='form-control' id='Foto' name='Foto' type='file' accept='image/*' />"
            "</div>"
        )

        # Mantener el nombre de la foto actual si no se sube una nueva
        form += (
            f"<input type='hidden' name='FotoActual' value='{html.escape(values['Foto'])}' />"
        )

        title = "Nuevo Médico" if is_new else f"Actualizar Médico #{id}"
        return (
            f"<h2 class='mb-3'>{html.escape(title)}</h2>"
            f"<form method='post' enctype='multipart/form-data'>"
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
        # No mostrar IdMedico ni IdUsuario en detalle
        form += self._input("Nombre", "Nombre", str(row.get("Nombre", "")), True)
        # Mostrar el nombre de la especialidad (campo alias Especialidad del JOIN)
        form += self._input("Especialidad", "Especialidad", str(row.get("Especialidad", "")), True)
        # No mostrar IdUsuario en el detalle

        # Mostrar la foto en lugar del nombre del archivo
        foto = str(row.get("Foto", "") or "")
        if foto:
            form += (
                "<div class='mb-3'>"
                "<label class='form-label'>Foto</label>"
                f"<div><img src='/static/img/usuarios/{html.escape(foto)}' "
                "class='img-thumbnail' style='max-width: 150px;' "
                "onerror=\"this.style.display='none'\" /></div>"
                "</div>"
            )
        else:
            form += self._input("Foto", "Foto", "Sin foto", True)

        return (
            f"<h2 class='mb-3'>Detalle Médico #{id}</h2>"
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
        especialidad = (form_data.get("Especialidad") or "").strip()
        id_usuario_s = (form_data.get("IdUsuario") or "").strip()
        id_usuario = int(id_usuario_s) if id_usuario_s else None

        # Manejo de la foto: si se sube una nueva, se guarda en static/img/usuarios.
        # Si no, se mantiene la foto actual.
        existing_foto = (form_data.get("FotoActual") or form_data.get("Foto") or "").strip()
        foto_filename = existing_foto

        try:
            file = request.files.get("Foto")  # type: ignore[attr-defined]
        except Exception:
            file = None

        if file and getattr(file, "filename", ""):
            filename = secure_filename(file.filename)
            if filename:
                upload_dir = Path(current_app.static_folder) / "img" / "usuarios"  # type: ignore[attr-defined]
                upload_dir.mkdir(parents=True, exist_ok=True)
                file_path = upload_dir / filename
                file.save(str(file_path))
                foto_filename = filename

        try:
            cur = self.cn.cursor()
            if op == "new":
                cur.execute(self.sql_insert, (nombre, especialidad, id_usuario, foto_filename))
                self.cn.commit()
                cur.close()
                return self._msg_success("Médico creado correctamente")

            if op == "act":
                cur.execute(self.sql_update, (nombre, especialidad, id_usuario, foto_filename, id_))
                self.cn.commit()
                cur.close()
                return self._msg_success("Médico actualizado correctamente")

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
            return self._msg_success("Médico eliminado correctamente")
        except Exception as ex:
            return self._msg_error(f"Error SQL: {ex}")
