from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Any, Dict, List, Tuple

from flask import current_app, request
from werkzeug.utils import secure_filename


class Paciente:

    table_name = "pacientes"
    pk = "IdPaciente"
    title = "Pacientes"
    path = "/pacientes"

    def __init__(self, cn):
        self.cn = cn

        self.IdPaciente: int | None = None
        self.IdUsuario: int | None = None
        self.Nombre: str = ""
        self.Cedula: str = ""
        self.Edad: int | None = None
        self.Genero: str = ""
        self.Estatura_cm: float | None = None
        self.Peso_kg: float | None = None
        self.Foto: str = ""

        self.sql_list = (
            "SELECT IdPaciente, IdUsuario, Nombre, Cedula, Edad, Genero, "
            "`Estatura (cm)` AS Estatura_cm, `Peso (kg)` AS Peso_kg, Foto "
            "FROM pacientes ORDER BY IdPaciente DESC"
        )
        self.sql_detail = (
            "SELECT IdPaciente, IdUsuario, Nombre, Cedula, Edad, Genero, "
            "`Estatura (cm)` AS Estatura_cm, `Peso (kg)` AS Peso_kg, Foto "
            "FROM pacientes WHERE IdPaciente=%s"
        )
        self.sql_insert = (
            "INSERT INTO pacientes(IdUsuario, Nombre, Cedula, Edad, Genero, `Estatura (cm)`, `Peso (kg)`, Foto) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
        )
        self.sql_update = (
            "UPDATE pacientes SET IdUsuario=%s, Nombre=%s, Cedula=%s, Edad=%s, Genero=%s, "
            "`Estatura (cm)`=%s, `Peso (kg)`=%s, Foto=%s WHERE IdPaciente=%s"
        )
        self.sql_delete = "DELETE FROM pacientes WHERE IdPaciente=%s"

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

    def _select(self, name: str, label: str, options: list[dict[str, Any]], selected: str, disabled: bool) -> str:
        dis = " disabled" if disabled else ""
        html_out = '<div class="mb-3">'
        html_out += f'<label class="form-label" for="{html.escape(name)}">{html.escape(label)}</label>'
        html_out += f'<select class="form-select" id="{html.escape(name)}" name="{html.escape(name)}"{dis}>'
        html_out += "<option value=''>Seleccione...</option>"
        for opt in options:
            oid = str(opt.get("IdUsuario", ""))
            oname = str(opt.get("Nombre", ""))
            sel = " selected" if oid and oid == (selected or "") else ""
            html_out += f"<option value='{html.escape(oid)}'{sel}>{html.escape(oname)}</option>"
        html_out += "</select></div>"
        return html_out

    def _select_simple(self, name: str, label: str, options: list[str], selected: str, disabled: bool) -> str:
        dis = " disabled" if disabled else ""
        html_out = '<div class="mb-3">'
        html_out += f'<label class="form-label" for="{html.escape(name)}">{html.escape(label)}</label>'
        html_out += f'<select class="form-select" id="{html.escape(name)}" name="{html.escape(name)}"{dis}>'
        html_out += "<option value=''>Seleccione...</option>"
        for opt in options:
            sel = " selected" if (opt or "") == (selected or "") else ""
            html_out += f"<option value='{html.escape(opt)}'{sel}>{html.escape(opt)}</option>"
        html_out += "</select></div>"
        return html_out

    def _validar_cedula_ec(self, cedula: str) -> bool:
        c = (cedula or "").strip()
        if len(c) != 10 or not c.isdigit():
            return False

        # Columna `Cedula` es INT UNSIGNED: evitar valores fuera de rango.
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

    def _validar_nombre_paciente(self, nombre: str) -> bool:
        # Solo letras (incluye tildes/ñ) y un espacio: Nombre Apellido
        n = " ".join((nombre or "").strip().split())
        parts = [p for p in n.split(" ") if p]
        if len(parts) != 2:
            return False
        import re

        rx = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ]+$")
        if not all(rx.match(p) for p in parts):
            return False
        # Primera letra de cada palabra en mayúscula
        return all(p[0].isupper() for p in parts)

    def _get_usuarios_disponibles_paciente(self, include_id: int | None = None) -> list[dict[str, Any]]:
        """Usuarios con rol Paciente (3) que no estén usados por paciente ni médico."""

        cur = self.cn.cursor(dictionary=True)
        if include_id:
            cur.execute(
                "SELECT u.IdUsuario, u.Nombre FROM usuarios u WHERE u.Rol=3 AND u.IdUsuario=%s",
                (include_id,),
            )
            row = cur.fetchone()
            cur.close()
            return [row] if row else []

        cur.execute(
            "SELECT u.IdUsuario, u.Nombre "
            "FROM usuarios u "
            "LEFT JOIN pacientes p ON u.IdUsuario = p.IdUsuario "
            "LEFT JOIN medicos m ON u.IdUsuario = m.IdUsuario "
            "WHERE u.Rol=3 AND p.IdUsuario IS NULL AND m.IdUsuario IS NULL "
            "ORDER BY u.Nombre"
        )
        rows = cur.fetchall() or []
        cur.close()
        return rows

    def get_list(self) -> str:
        cur = self.cn.cursor(dictionary=True)
        cur.execute(self.sql_list)
        rows: List[Dict[str, Any]] = cur.fetchall() or []
        cur.close()

        d_new = self._d_encode("new", 0)
        headers = [
            "Nombre",
            "Cedula",
            "Edad",
            "Genero",
            "Estatura_cm",
            "Peso_kg",
            "Foto",
            "Acciones",
        ]
        thead = "".join(f"<th>{h}</th>" for h in headers)

        tbody = ""
        for r in rows:
            pk = int(r["IdPaciente"])
            d_act = self._d_encode("act", pk)
            d_det = self._d_encode("det", pk)
            d_del = self._d_encode("del", pk)

            foto = str(r.get("Foto") or "")
            foto_html = ""
            if foto:
                foto_html = (
                    f"<div><img src='/static/img/usuarios/{html.escape(foto)}' width='50' "
                    "onerror=\"this.style.display='none'\" /></div>"
                    f"<small class='text-muted'>{html.escape(foto)}</small>"
                )

            tbody += (
                "<tr>"
                f"<td>{html.escape(str(r.get('Nombre','')))}</td>"
                f"<td>{html.escape(str(r.get('Cedula','')))}</td>"
                f"<td>{html.escape(str(r.get('Edad','')))}</td>"
                f"<td>{html.escape(str(r.get('Genero','')))}</td>"
                f"<td>{html.escape(str(r.get('Estatura_cm','')))}</td>"
                f"<td>{html.escape(str(r.get('Peso_kg','')))}</td>"
                f"<td>{foto_html}</td>"
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
            f"<thead class='veris-tabla-thead'><tr>{thead}</tr></thead>"
            f"<tbody class='veris-tabla-body-content'>{tbody}</tbody>"
            "</table>"
            "</div>"
            "</main>"
        )

    def get_form(self, id: int = 0) -> str:
        is_new = id == 0
        op = "new" if is_new else "act"

        values = {
            "IdPaciente": "",
            "IdUsuario": "",
            "Nombre": "",
            "Cedula": "",
            "Edad": "",
            "Genero": "",
            "Estatura_cm": "",
            "Peso_kg": "",
            "Foto": "",
        }

        if not is_new:
            cur = self.cn.cursor(dictionary=True)
            cur.execute(self.sql_detail, (id,))
            row = cur.fetchone()
            cur.close()
            if not row:
                return self._msg_error("Registro no encontrado")
            for k in values:
                values[k] = "" if row.get(k) is None else str(row.get(k))

        d = self._d_encode(op, id)
        form = ""

        # Usuario asociado
        if is_new:
            usuarios = self._get_usuarios_disponibles_paciente()
            if not usuarios:
                form += (
                    "<div class='alert alert-warning' role='alert'>"
                    "No hay usuarios con rol Paciente disponibles (sin asignación previa)."
                    "</div>"
                )
            form += self._select("IdUsuario", "Usuario", usuarios, values["IdUsuario"], False)
        else:
            try:
                include_id = int(values["IdUsuario"]) if values["IdUsuario"] else None
            except Exception:
                include_id = None
            usuarios = self._get_usuarios_disponibles_paciente(include_id=include_id)
            form += self._select("IdUsuario", "Usuario", usuarios, values["IdUsuario"], True)
            if values["IdUsuario"]:
                form += f"<input type='hidden' name='IdUsuario' value='{html.escape(values['IdUsuario'])}' />"

        # Restricción edición: solo Edad/Estatura/Peso/Foto editables
        nombre_ro = " readonly" if not is_new else ""
        cedula_ro = " readonly" if not is_new else ""

        form += (
            "<div class='mb-3'>"
            "<label class='form-label' for='Nombre'>Nombre</label>"
            f"<input class='form-control' id='Nombre' name='Nombre' type='text' value='{html.escape(values['Nombre'])}'{nombre_ro} />"
            "</div>"
        )
        form += (
            "<div class='mb-3'>"
            "<label class='form-label' for='Cedula'>Cedula</label>"
            f"<input class='form-control' id='Cedula' name='Cedula' type='text' maxlength='10' inputmode='numeric' value='{html.escape(values['Cedula'])}'{cedula_ro} />"
            "</div>"
        )

        # Edad
        form += (
            "<div class='mb-3'>"
            "<label class='form-label' for='Edad'>Edad</label>"
            f"<input class='form-control' id='Edad' name='Edad' type='number' min='0' max='120' step='1' value='{html.escape(values['Edad'])}' />"
            "</div>"
        )

        # Género (select)
        if is_new:
            form += self._select_simple("Genero", "Género", ["Masculino", "Femenino"], values["Genero"], False)
        else:
            form += self._select_simple("Genero", "Género", ["Masculino", "Femenino"], values["Genero"], True)
            form += f"<input type='hidden' name='Genero' value='{html.escape(values['Genero'])}' />"

        # Estatura / Peso
        form += (
            "<div class='mb-3'>"
            "<label class='form-label' for='Estatura_cm'>Estatura (cm)</label>"
            f"<input class='form-control' id='Estatura_cm' name='Estatura_cm' type='number' min='30' max='250' step='0.01' value='{html.escape(values['Estatura_cm'])}' />"
            "</div>"
        )
        form += (
            "<div class='mb-3'>"
            "<label class='form-label' for='Peso_kg'>Peso (kg)</label>"
            f"<input class='form-control' id='Peso_kg' name='Peso_kg' type='number' min='0' max='300' step='0.01' value='{html.escape(values['Peso_kg'])}' />"
            "</div>"
        )

        # Campo para subir nueva foto (muestra input file en lugar del nombre)
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

        title = "Nuevo Paciente" if is_new else f"Actualizar Paciente"
        return (
            f"<h2 class='mb-3'>{html.escape(title)}</h2>"
            f"<form method='post' enctype='multipart/form-data'>"
            f"<input type='hidden' name='d' value='{html.escape(d)}' />"
            f"{form}"
            "<button class='btn btn-primary' type='submit'>Guardar</button> "
            f"<a class='btn btn-outline-secondary' href='{self.path}'>Volver</a>"
            "</form>"
            "<script src='/static/js/paciente-validaciones.js'></script>"
        )

    def get_detail(self, id: int) -> str:
        cur = self.cn.cursor(dictionary=True)
        cur.execute(self.sql_detail, (id,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return self._msg_error("Registro no encontrado")

        values = {k: ("" if row.get(k) is None else str(row.get(k))) for k in row.keys()}

        form = ""
        # No mostrar IdPaciente ni IdUsuario en detalle
        form += self._input("Nombre", "Nombre", str(values.get("Nombre", "")), True)
        form += self._input("Cedula", "Cedula", str(values.get("Cedula", "")), True)
        form += self._input("Edad", "Edad", str(values.get("Edad", "")), True, "number")
        form += self._input("Genero", "Genero", str(values.get("Genero", "")), True)
        form += self._input("Estatura_cm", "Estatura (cm)", str(values.get("Estatura_cm", "")), True, "number")
        form += self._input("Peso_kg", "Peso (kg)", str(values.get("Peso_kg", "")), True, "number")

        # Mostrar la foto en lugar del nombre del archivo
        foto = str(values.get("Foto", "") or "")
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
            f"<h2 class='mb-3'>Detalle Paciente</h2>"
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

        def _i(name: str) -> int | None:
            v = (form_data.get(name) or "").strip()
            return int(v) if v else None

        def _f(name: str) -> float | None:
            v = (form_data.get(name) or "").strip()
            return float(v) if v else None

        id_usuario = _i("IdUsuario")
        if not id_usuario:
            return self._msg_error("Debe seleccionar un usuario (rol Paciente)")

        # Validar que el usuario sea rol Paciente y no esté usado (en creación)
        curv = self.cn.cursor(dictionary=True)
        curv.execute(
            "SELECT u.IdUsuario FROM usuarios u WHERE u.IdUsuario=%s AND u.Rol=3",
            (id_usuario,),
        )
        if not curv.fetchone():
            curv.close()
            return self._msg_error("El usuario seleccionado no es válido para Paciente")

        if op == "new":
            curv.execute("SELECT 1 FROM pacientes WHERE IdUsuario=%s LIMIT 1", (id_usuario,))
            if curv.fetchone():
                curv.close()
                return self._msg_error("El usuario seleccionado ya está asignado a un paciente")
            curv.execute("SELECT 1 FROM medicos WHERE IdUsuario=%s LIMIT 1", (id_usuario,))
            if curv.fetchone():
                curv.close()
                return self._msg_error("El usuario seleccionado ya está asignado a un médico")

        curv.close()

        # Manejo de la foto: si se sube una nueva, se guarda en static/img/usuarios.
        # Si no, se mantiene la foto actual.
        existing_foto = (form_data.get("FotoActual") or form_data.get("Foto") or "").strip()
        foto_filename = existing_foto

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

        nombre = (form_data.get("Nombre") or "").strip()
        cedula = (form_data.get("Cedula") or "").strip()
        edad = _i("Edad")
        genero = (form_data.get("Genero") or "").strip()
        estatura = _f("Estatura_cm")
        peso = _f("Peso_kg")

        # Validaciones
        if op == "new":
            if not self._validar_nombre_paciente(nombre):
                return self._msg_error("Nombre inválido. Use el formato: Nombre Apellido (solo letras, iniciales en mayúscula)")
            if not self._validar_cedula_ec(cedula):
                return self._msg_error("Cédula inválida o fuera de rango. Ingrese una cédula ecuatoriana válida")
            if genero not in ("Masculino", "Femenino"):
                return self._msg_error("Género inválido. Seleccione Masculino o Femenino")
        else:
            # En edición, no se permiten cambios en nombre/cedula/genero/idUsuario.
            curx = self.cn.cursor(dictionary=True)
            curx.execute(self.sql_detail, (id_,))
            row = curx.fetchone()
            curx.close()
            if not row:
                return self._msg_error("Registro no encontrado")
            id_usuario = int(row.get("IdUsuario") or id_usuario)
            nombre = str(row.get("Nombre") or "")
            cedula = str(row.get("Cedula") or "")
            genero = str(row.get("Genero") or "")

        if edad is None or edad < 0 or edad > 120:
            return self._msg_error("Edad inválida. Debe estar entre 0 y 120")
        if estatura is not None and (estatura < 30 or estatura > 250):
            return self._msg_error("Estatura inválida. Debe estar entre 30 y 250 cm")
        if peso is not None and (peso < 0 or peso > 300):
            return self._msg_error("Peso inválido. Debe estar entre 0 y 300 kg")

        payload = (
            id_usuario,
            nombre,
            cedula,
            edad,
            genero,
            estatura,
            peso,
            foto_filename,
        )

        try:
            cur = self.cn.cursor()
            if op == "new":
                cur.execute(self.sql_insert, payload)
                self.cn.commit()
                cur.close()
                return self._msg_success("Paciente creado correctamente")

            if op == "act":
                cur.execute(self.sql_update, (*payload, id_))
                self.cn.commit()
                cur.close()
                return self._msg_success("Paciente actualizado correctamente")

            cur.close()
            return self._msg_error("Operación no permitida")
        except Exception as ex:
            return self._msg_error(f"Error SQL: {ex}")

    def delete(self, id: int) -> str:
        try:
            curv = self.cn.cursor(dictionary=True)
            curv.execute("SELECT 1 FROM consultas WHERE IdPaciente=%s LIMIT 1", (id,))
            if curv.fetchone():
                curv.close()
                return self._msg_error("No se puede eliminar el paciente porque tiene consultas registradas")
            curv.close()

            cur = self.cn.cursor()
            cur.execute(self.sql_delete, (id,))
            self.cn.commit()
            cur.close()
            return self._msg_success("Paciente eliminado correctamente")
        except Exception as ex:
            return self._msg_error(f"Error SQL: {ex}")
