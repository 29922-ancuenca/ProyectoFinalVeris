from __future__ import annotations

import base64
import html
from typing import Any, Dict, List, Tuple


class Consulta:
    """CRUD POO para la tabla `consultas`.

    Tabla: consultas(IdConsulta, IdMedico, IdPaciente, FechaConsulta, HI, HF, Diagnostico)
    """

    table_name = "consultas"
    pk = "IdConsulta"
    title = "Consultas"
    path = "/consultas"

    def __init__(self, cn):
        self.cn = cn

        self.IdConsulta: int | None = None
        self.IdMedico: int | None = None
        self.IdPaciente: int | None = None
        self.FechaConsulta: str = ""
        self.HI: str = ""
        self.HF: str = ""
        self.Diagnostico: str = ""

        # JOINs para mostrar los nombres de médico y paciente en lugar de sus IDs
        self.sql_list = (
            "SELECT c.IdConsulta, c.IdMedico, c.IdPaciente, "
            "m.Nombre AS NombreMedico, p.Nombre AS NombrePaciente, "
            "c.FechaConsulta, c.HI, c.HF, c.Diagnostico "
            "FROM consultas c "
            "LEFT JOIN medicos m ON c.IdMedico = m.IdMedico "
            "LEFT JOIN pacientes p ON c.IdPaciente = p.IdPaciente "
            "ORDER BY c.IdConsulta DESC"
        )
        self.sql_detail = (
            "SELECT c.IdConsulta, c.IdMedico, c.IdPaciente, "
            "m.Nombre AS NombreMedico, p.Nombre AS NombrePaciente, "
            "c.FechaConsulta, c.HI, c.HF, c.Diagnostico "
            "FROM consultas c "
            "LEFT JOIN medicos m ON c.IdMedico = m.IdMedico "
            "LEFT JOIN pacientes p ON c.IdPaciente = p.IdPaciente "
            "WHERE c.IdConsulta=%s"
        )
        self.sql_insert = (
            "INSERT INTO consultas(IdMedico, IdPaciente, FechaConsulta, HI, HF, Diagnostico) "
            "VALUES(%s,%s,%s,%s,%s,%s)"
        )
        self.sql_update = (
            "UPDATE consultas SET IdMedico=%s, IdPaciente=%s, FechaConsulta=%s, HI=%s, HF=%s, Diagnostico=%s "
            "WHERE IdConsulta=%s"
        )
        self.sql_delete = "DELETE FROM consultas WHERE IdConsulta=%s"

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

    def _textarea(self, name: str, label: str, value: str, disabled: bool) -> str:
        dis = " disabled" if disabled else ""
        return (
            '<div class="mb-3">'
            f'<label class="form-label" for="{html.escape(name)}">{html.escape(label)}</label>'
            f'<textarea class="form-control" id="{html.escape(name)}" name="{html.escape(name)}" rows="4"{dis}>'
            f"{html.escape(value)}"
            "</textarea>"
            "</div>"
        )

    def get_list(self) -> str:
        cur = self.cn.cursor(dictionary=True)
        cur.execute(self.sql_list)
        rows: List[Dict[str, Any]] = cur.fetchall() or []
        cur.close()

        d_new = self._d_encode("new", 0)
        headers = ["Médico", "Paciente", "FechaConsulta", "HI", "HF", "Diagnostico", "Acciones"]
        thead = "".join(f"<th>{h}</th>" for h in headers)

        tbody = ""
        for r in rows:
            pk = int(r["IdConsulta"])
            d_act = self._d_encode("act", pk)
            d_det = self._d_encode("det", pk)
            d_del = self._d_encode("del", pk)
            diag = str(r.get("Diagnostico") or "")
            tbody += (
                "<tr>"
                f"<td>{html.escape(str(r.get('NombreMedico','')))}</td>"
                f"<td>{html.escape(str(r.get('NombrePaciente','')))}</td>"
                f"<td>{html.escape(str(r.get('FechaConsulta','')))}</td>"
                f"<td>{html.escape(str(r.get('HI','')))}</td>"
                f"<td>{html.escape(str(r.get('HF','')))}</td>"
                f"<td>{html.escape(diag[:60] + ('...' if len(diag) > 60 else ''))}</td>"
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
        disabled_pk = (not is_new)

        values = {
            "IdConsulta": "",
            "IdMedico": "",
            "IdPaciente": "",
            "FechaConsulta": "",
            "HI": "",
            "HF": "",
            "Diagnostico": "",
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
        form += self._input("IdConsulta", "IdConsulta", values["IdConsulta"], disabled_pk, "number")
        form += self._input("IdMedico", "IdMedico", values["IdMedico"], False, "number")
        form += self._input("IdPaciente", "IdPaciente", values["IdPaciente"], False, "number")
        form += self._input("FechaConsulta", "FechaConsulta", values["FechaConsulta"], False, "date")
        form += self._input("HI", "HI", values["HI"], False, "time")
        form += self._input("HF", "HF", values["HF"], False, "time")
        form += self._textarea("Diagnostico", "Diagnostico", values["Diagnostico"], False)

        title = "Nueva Consulta" if is_new else f"Actualizar Consulta #{id}"
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
        form += self._input("IdConsulta", "IdConsulta", str(row.get("IdConsulta", "")), True, "number")
        form += self._input("IdMedico", "IdMedico", str(row.get("IdMedico", "")), True, "number")
        form += self._input("IdPaciente", "IdPaciente", str(row.get("IdPaciente", "")), True, "number")
        form += self._input("FechaConsulta", "FechaConsulta", str(row.get("FechaConsulta", "")), True, "date")
        form += self._input("HI", "HI", str(row.get("HI", "")), True, "time")
        form += self._input("HF", "HF", str(row.get("HF", "")), True, "time")
        form += self._textarea("Diagnostico", "Diagnostico", str(row.get("Diagnostico", "")), True)

        return (
            f"<h2 class='mb-3'>Detalle Consulta #{id}</h2>"
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

        payload = (
            _i("IdMedico"),
            _i("IdPaciente"),
            (form_data.get("FechaConsulta") or "").strip(),
            (form_data.get("HI") or "").strip(),
            (form_data.get("HF") or "").strip(),
            (form_data.get("Diagnostico") or "").strip(),
        )

        try:
            cur = self.cn.cursor()
            if op == "new":
                cur.execute(self.sql_insert, payload)
                self.cn.commit()
                cur.close()
                return self._msg_success("Consulta creada correctamente")

            if op == "act":
                cur.execute(self.sql_update, (*payload, id_))
                self.cn.commit()
                cur.close()
                return self._msg_success("Consulta actualizada correctamente")

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
            return self._msg_success("Consulta eliminada correctamente")
        except Exception as ex:
            return self._msg_error(f"Error SQL: {ex}")
