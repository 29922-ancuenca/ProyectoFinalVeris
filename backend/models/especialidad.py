from __future__ import annotations

import base64
import html
from typing import Any, Dict, List, Tuple


class Especialidad:
    """CRUD POO para la tabla `especialidades`.

    Tabla: especialidades(IdEsp, Descripcion, Dias, Franja_HI, Franja_HF)
    """

    table_name = "especialidades"
    pk = "IdEsp"
    title = "Especialidades"
    path = "/especialidades"

    def __init__(self, cn):
        self.cn = cn

        self.IdEsp: int | None = None
        self.Descripcion: str = ""
        self.Dias: str = ""
        self.Franja_HI: str = ""
        self.Franja_HF: str = ""

        self.sql_list = "SELECT IdEsp, Descripcion, Dias, Franja_HI, Franja_HF FROM especialidades ORDER BY IdEsp DESC"
        self.sql_detail = "SELECT IdEsp, Descripcion, Dias, Franja_HI, Franja_HF FROM especialidades WHERE IdEsp=%s"
        self.sql_insert = "INSERT INTO especialidades(Descripcion, Dias, Franja_HI, Franja_HF) VALUES(%s,%s,%s,%s)"
        self.sql_update = "UPDATE especialidades SET Descripcion=%s, Dias=%s, Franja_HI=%s, Franja_HF=%s WHERE IdEsp=%s"
        self.sql_delete = "DELETE FROM especialidades WHERE IdEsp=%s"

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

    def _dias_selector(self, selected: str, disabled: bool) -> str:
        """UI de selección de días mediante checkboxes.

        Guarda en POST múltiples valores con name="Dias" y valores: L,M,X,J,V,S,D
        """

        selected_set = {c for c in (selected or "") if c in "LMXJV"}
        dis_attr = " disabled" if disabled else ""

        # Orden y etiquetas
        days = [
            ("L", "Lunes"),
            ("M", "Martes"),
            ("X", "Miércoles"),
            ("J", "Jueves"),
            ("V", "Viernes"),
        ]

        items = ""
        for code, label in days:
            checked = " checked" if code in selected_set else ""
            cid = f"dias_{code}"
            items += (
                '<div class="col-6 col-md-4">'
                '<div class="form-check">'
                f'<input class="form-check-input" type="checkbox" id="{html.escape(cid)}" name="Dias" value="{html.escape(code)}"{checked}{dis_attr}>'
                f'<label class="form-check-label" for="{html.escape(cid)}">{html.escape(label)}</label>'
                "</div>"
                "</div>"
            )

        buttons = ""
        script = ""
        if not disabled:
            buttons = (
                '<div class="mt-3 d-flex gap-2">'
                '<button type="button" class="btn btn-outline-primary btn-sm" id="btnDiasLV">Lunes a Viernes</button>'
                '<button type="button" class="btn btn-outline-danger btn-sm" id="btnDiasClear">Limpiar</button>'
                "</div>"
            )
            script = (
                "<script>\n"
                "document.addEventListener('DOMContentLoaded', function () {\n"
                "  var btnLV = document.getElementById('btnDiasLV');\n"
                "  var btnClr = document.getElementById('btnDiasClear');\n"
                "  function setDias(codes) {\n"
                "    var set = {};\n"
                "    (codes || []).forEach(function (c) { set[c] = true; });\n"
                "    document.querySelectorAll('input[name=\"Dias\"]').forEach(function (el) {\n"
                "      el.checked = !!set[el.value];\n"
                "    });\n"
                "  }\n"
                "  if (btnLV) btnLV.addEventListener('click', function () { setDias(['L','M','X','J','V']); });\n"
                "  if (btnClr) btnClr.addEventListener('click', function () { setDias([]); });\n"
                "});\n"
                "</script>"
            )

        return (
            '<div class="mb-3">'
            '<label class="form-label">Días de Atención</label>'
            '<div class="card shadow-sm">'
            '<div class="card-body">'
            '<div class="row g-2">'
            f"{items}"
            "</div>"
            f"{buttons}"
            "</div>"
            "</div>"
            f"{script}"
            "</div>"
        )

    def _fmt_time_value(self, value: Any) -> str:
        """Convierte valores TIME de MySQL a formato válido para <input type="time"> (HH:MM).

        Algunos conectores devuelven TIME como:
        - datetime.time
        - str '08:00:00', '8:00:00', '08:00', '8:00'
        """

        if value is None:
            return ""

        # datetime.time
        if hasattr(value, "hour") and hasattr(value, "minute"):
            try:
                hh = int(getattr(value, "hour"))
                mm = int(getattr(value, "minute"))
                return f"{hh:02d}:{mm:02d}"
            except Exception:
                pass

        s = str(value).strip()
        if not s:
            return ""

        # Si viene con segundos, recortar
        # Acepta H:MM:SS o HH:MM:SS
        parts = s.split(":")
        if len(parts) >= 2:
            try:
                hh = int(parts[0])
                mm = int(parts[1])
                return f"{hh:02d}:{mm:02d}"
            except Exception:
                return ""

        return ""

    def _hhmm_to_minutes(self, hhmm: str) -> int | None:
        s = (hhmm or "").strip()
        if not s:
            return None
        parts = s.split(":")
        if len(parts) < 2:
            return None
        try:
            h = int(parts[0])
            m = int(parts[1])
        except Exception:
            return None
        if h < 0 or h > 23 or m < 0 or m > 59:
            return None
        return h * 60 + m

    def get_list(self) -> str:
        cur = self.cn.cursor(dictionary=True)
        cur.execute(self.sql_list)
        rows: List[Dict[str, Any]] = cur.fetchall() or []
        cur.close()

        d_new = self._d_encode("new", 0)
        headers = ["Descripcion", "Dias", "Franja_HI", "Franja_HF", "Acciones"]
        thead = "".join(f"<th>{h}</th>" for h in headers)

        tbody = ""
        for r in rows:
            pk = int(r["IdEsp"])
            d_act = self._d_encode("act", pk)
            d_det = self._d_encode("det", pk)
            d_del = self._d_encode("del", pk)
            tbody += (
                "<tr>"
                f"<td>{html.escape(str(r.get('Descripcion','')))}</td>"
                f"<td>{html.escape(str(r.get('Dias','')))}</td>"
                f"<td>{html.escape(str(r.get('Franja_HI','')))}</td>"
                f"<td>{html.escape(str(r.get('Franja_HF','')))}</td>"
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
        values = {"IdEsp": "", "Descripcion": "", "Dias": "", "Franja_HI": "", "Franja_HF": ""}
        if not is_new:
            cur = self.cn.cursor(dictionary=True)
            cur.execute(self.sql_detail, (id,))
            row = cur.fetchone()
            cur.close()
            if not row:
                return self._msg_error("Registro no encontrado")
            for k in values:
                values[k] = "" if row.get(k) is None else str(row.get(k))

        values["Franja_HI"] = self._fmt_time_value(values["Franja_HI"])
        values["Franja_HF"] = self._fmt_time_value(values["Franja_HF"])

        d = self._d_encode(op, id)
        form = ""
        # No mostrar IdEsp en el formulario (se maneja internamente con d)
        form += self._input("Descripcion", "Descripcion", values["Descripcion"], False)
        form += self._dias_selector(values["Dias"], False)
        form += self._input("Franja_HI", "Franja_HI", values["Franja_HI"], False, "time")
        form += self._input("Franja_HF", "Franja_HF", values["Franja_HF"], False, "time")

        title = "Nueva Especialidad" if is_new else "Actualizar Especialidad"
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

        franja_hi = self._fmt_time_value(row.get("Franja_HI"))
        franja_hf = self._fmt_time_value(row.get("Franja_HF"))

        form = ""
        # No mostrar IdEsp en detalle
        form += self._input("Descripcion", "Descripcion", str(row.get("Descripcion", "")), True)
        form += self._dias_selector(str(row.get("Dias", "")), True)
        form += self._input("Franja_HI", "Franja_HI", franja_hi, True, "time")
        form += self._input("Franja_HF", "Franja_HF", franja_hf, True, "time")

        return (
            f"<h2 class='mb-3'>Detalle Especialidad</h2>"
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

        descripcion = (form_data.get("Descripcion") or "").strip()
        # Nuevo UI: checkboxes con name="Dias" (multi-valor)
        selected_days = []
        try:
            selected_days = list(form_data.getlist("Dias"))  # type: ignore[attr-defined]
        except Exception:
            selected_days = []

        # Compatibilidad: si por alguna razón viene como texto
        dias_text = (form_data.get("Dias") or "").strip()

        order = ["L", "M", "X", "J", "V"]
        if selected_days:
            selected_set = {str(x).strip().upper() for x in selected_days}
            dias = "".join([c for c in order if c in selected_set])
        else:
            dias = "".join([c for c in order if c in (dias_text or "").upper()])
        franja_hi = (form_data.get("Franja_HI") or "").strip()
        franja_hf = (form_data.get("Franja_HF") or "").strip()

        if not dias:
            return self._msg_error("Debe seleccionar al menos un día de atención")

        hi_min = self._hhmm_to_minutes(franja_hi)
        hf_min = self._hhmm_to_minutes(franja_hf)
        if hi_min is None or hf_min is None:
            return self._msg_error("Debe ingresar Franja_HI y Franja_HF en formato HH:MM")

        if hi_min >= hf_min:
            return self._msg_error("La Franja_HI debe ser menor que la Franja_HF")

        min_allowed = 8 * 60
        max_allowed = 18 * 60
        if hi_min < min_allowed or hf_min > max_allowed:
            return self._msg_error("El horario debe estar dentro de 08:00 a 18:00")

        try:
            cur = self.cn.cursor()
            if op == "new":
                cur.execute(self.sql_insert, (descripcion, dias, franja_hi, franja_hf))
                self.cn.commit()
                cur.close()
                return self._msg_success("Especialidad creada correctamente")

            if op == "act":
                cur.execute(self.sql_update, (descripcion, dias, franja_hi, franja_hf, id_))
                self.cn.commit()
                cur.close()
                return self._msg_success("Especialidad actualizada correctamente")

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
            return self._msg_success("Especialidad eliminada correctamente")
        except Exception as ex:
            return self._msg_error(f"Error SQL: {ex}")
