from __future__ import annotations

import base64
import html
from typing import Any, Dict, List, Tuple


class Paciente:
    """CRUD POO para la tabla `pacientes`.

    Tabla: pacientes(
        IdPaciente, IdUsuario, Nombre, Cedula, Edad, Genero,
        Estatura (cm), Peso (kg), Foto
    )

    Nota: columnas con espacios/paréntesis se consultan con backticks.
    """

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
        links = [
            ("Inicio", "/"),
            ("Pacientes", "/pacientes"),
            ("Médicos", "/medicos"),
            ("Especialidades", "/especialidades"),
            ("Medicamentos", "/medicamentos"),
            ("Consultas", "/consultas"),
            ("Recetas", "/recetas"),
            ("Roles", "/roles"),
            ("Usuarios", "/usuarios"),
        ]
        items = "".join(
            f'<li class="nav-item"><a class="nav-link" href="{html.escape(href)}">{html.escape(text)}</a></li>'
            for text, href in links
        )
        return (
            '<nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm py-2">'
            '<div class="container-fluid px-4">'
            '<a class="navbar-brand" href="/">VERIS</a>'
            '<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#menuPrincipal"'
            ' aria-controls="menuPrincipal" aria-expanded="false" aria-label="Alternar navegación">'
            '<span class="navbar-toggler-icon"></span></button>'
            '<div class="collapse navbar-collapse" id="menuPrincipal">'
            f'<ul class="navbar-nav me-auto mb-2 mb-lg-0">{items}</ul>'
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
        headers = [
            "IdPaciente",
            "IdUsuario",
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
                f"<td>{pk}</td>"
                f"<td>{html.escape(str(r.get('IdUsuario','')))}</td>"
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
                f"<a class='btn btn-sm btn-danger' href='{self.path}?d={d_del}' onclick=\"return confirm('¿Eliminar este registro?');\">Eliminar</a>"
                "</td>"
                "</tr>"
            )

        return (
            f"<h2 class='mb-3'>{html.escape(self.title)}</h2>"
            f"<p><a class='btn btn-success' href='{self.path}?d={d_new}'>Nuevo</a></p>"
            "<table class='table table-bordered table-striped'>"
            f"<thead><tr>{thead}</tr></thead>"
            f"<tbody>{tbody}</tbody>"
            "</table>"
        )

    def get_form(self, id: int = 0) -> str:
        is_new = id == 0
        op = "new" if is_new else "act"
        disabled_pk = (not is_new)

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
        form += self._input("IdPaciente", "IdPaciente", values["IdPaciente"], disabled_pk, "number")
        form += self._input("IdUsuario", "IdUsuario", values["IdUsuario"], False, "number")
        form += self._input("Nombre", "Nombre", values["Nombre"], False)
        form += self._input("Cedula", "Cedula", values["Cedula"], False)
        form += self._input("Edad", "Edad", values["Edad"], False, "number")
        form += self._input("Genero", "Genero", values["Genero"], False)
        form += self._input("Estatura_cm", "Estatura (cm)", values["Estatura_cm"], False, "number")
        form += self._input("Peso_kg", "Peso (kg)", values["Peso_kg"], False, "number")
        form += self._input("Foto", "Foto (archivo en static/img/usuarios)", values["Foto"], False)

        title = "Nuevo Paciente" if is_new else f"Actualizar Paciente #{id}"
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

        values = {k: ("" if row.get(k) is None else str(row.get(k))) for k in row.keys()}

        form = ""
        form += self._input("IdPaciente", "IdPaciente", str(values.get("IdPaciente", "")), True, "number")
        form += self._input("IdUsuario", "IdUsuario", str(values.get("IdUsuario", "")), True, "number")
        form += self._input("Nombre", "Nombre", str(values.get("Nombre", "")), True)
        form += self._input("Cedula", "Cedula", str(values.get("Cedula", "")), True)
        form += self._input("Edad", "Edad", str(values.get("Edad", "")), True, "number")
        form += self._input("Genero", "Genero", str(values.get("Genero", "")), True)
        form += self._input("Estatura_cm", "Estatura (cm)", str(values.get("Estatura_cm", "")), True, "number")
        form += self._input("Peso_kg", "Peso (kg)", str(values.get("Peso_kg", "")), True, "number")
        form += self._input("Foto", "Foto", str(values.get("Foto", "")), True)

        return (
            f"<h2 class='mb-3'>Detalle Paciente #{id}</h2>"
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

        payload = (
            _i("IdUsuario"),
            (form_data.get("Nombre") or "").strip(),
            (form_data.get("Cedula") or "").strip(),
            _i("Edad"),
            (form_data.get("Genero") or "").strip(),
            _f("Estatura_cm"),
            _f("Peso_kg"),
            (form_data.get("Foto") or "").strip(),
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
            cur = self.cn.cursor()
            cur.execute(self.sql_delete, (id,))
            self.cn.commit()
            cur.close()
            return self._msg_success("Paciente eliminado correctamente")
        except Exception as ex:
            return self._msg_error(f"Error SQL: {ex}")
