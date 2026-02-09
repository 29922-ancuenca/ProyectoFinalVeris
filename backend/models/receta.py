from __future__ import annotations

import base64
import html
from typing import Any, Dict, List, Tuple


class Receta:
    """CRUD POO para la tabla `recetas`.

    Tabla: recetas(IdReceta, IdConsulta, IdMedicamento, Cantidad)
    """

    table_name = "recetas"
    pk = "IdReceta"
    title = "Recetas"
    path = "/recetas"

    def __init__(self, cn):
        self.cn = cn

        self.IdReceta: int | None = None
        self.IdConsulta: int | None = None
        self.IdMedicamento: int | None = None
        self.Cantidad: int | None = None

        # JOINs para mostrar el diagnóstico de la consulta y el nombre del medicamento
        self.sql_list = (
            "SELECT r.IdReceta, r.IdConsulta, r.IdMedicamento, r.Cantidad, "
            "c.Diagnostico AS Consulta, m.Nombre AS Medicamento "
            "FROM recetas r "
            "LEFT JOIN consultas c ON r.IdConsulta = c.IdConsulta "
            "LEFT JOIN medicamentos m ON r.IdMedicamento = m.IdMedicamento "
            "ORDER BY r.IdReceta DESC"
        )
        self.sql_detail = (
            "SELECT r.IdReceta, r.IdConsulta, r.IdMedicamento, r.Cantidad, "
            "c.Diagnostico AS Consulta, m.Nombre AS Medicamento "
            "FROM recetas r "
            "LEFT JOIN consultas c ON r.IdConsulta = c.IdConsulta "
            "LEFT JOIN medicamentos m ON r.IdMedicamento = m.IdMedicamento "
            "WHERE r.IdReceta=%s"
        )
        self.sql_insert = "INSERT INTO recetas(IdConsulta, IdMedicamento, Cantidad) VALUES(%s,%s,%s)"
        self.sql_update = "UPDATE recetas SET IdConsulta=%s, IdMedicamento=%s, Cantidad=%s WHERE IdReceta=%s"
        self.sql_delete = "DELETE FROM recetas WHERE IdReceta=%s"

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
        headers = ["Consulta", "Medicamento", "Cantidad", "Acciones"]
        thead = "".join(f"<th>{h}</th>" for h in headers)

        tbody = ""
        for r in rows:
            pk = int(r["IdReceta"])
            d_act = self._d_encode("act", pk)
            d_det = self._d_encode("det", pk)
            d_del = self._d_encode("del", pk)
            tbody += (
                "<tr>"
                f"<td>{html.escape(str(r.get('Consulta','')))}</td>"
                f"<td>{html.escape(str(r.get('Medicamento','')))}</td>"
                f"<td>{html.escape(str(r.get('Cantidad','')))}</td>"
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
        disabled_pk = (not is_new)

        values = {"IdReceta": "", "IdConsulta": "", "IdMedicamento": "", "Cantidad": ""}
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
        form += self._input("IdReceta", "IdReceta", values["IdReceta"], disabled_pk, "number")
        form += self._input("IdConsulta", "IdConsulta", values["IdConsulta"], False, "number")
        form += self._input("IdMedicamento", "IdMedicamento", values["IdMedicamento"], False, "number")
        form += self._input("Cantidad", "Cantidad", values["Cantidad"], False, "number")

        title = "Nueva Receta" if is_new else f"Actualizar Receta"
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
        form += self._input("IdReceta", "IdReceta", str(row.get("IdReceta", "")), True, "number")
        form += self._input("IdConsulta", "IdConsulta", str(row.get("IdConsulta", "")), True, "number")
        form += self._input("IdMedicamento", "IdMedicamento", str(row.get("IdMedicamento", "")), True, "number")
        form += self._input("Cantidad", "Cantidad", str(row.get("Cantidad", "")), True, "number")

        return (
            f"<h2 class='mb-3'>Detalle Receta</h2>"
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

        payload = (_i("IdConsulta"), _i("IdMedicamento"), _i("Cantidad"))

        try:
            cur = self.cn.cursor()
            if op == "new":
                cur.execute(self.sql_insert, payload)
                self.cn.commit()
                cur.close()
                return self._msg_success("Receta creada correctamente")

            if op == "act":
                cur.execute(self.sql_update, (*payload, id_))
                self.cn.commit()
                cur.close()
                return self._msg_success("Receta actualizada correctamente")

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
            return self._msg_success("Receta eliminada correctamente")
        except Exception as ex:
            return self._msg_error(f"Error SQL: {ex}")
