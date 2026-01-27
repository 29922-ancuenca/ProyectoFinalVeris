from __future__ import annotations

from typing import Any, Dict, List, Optional

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from database.connection import fetch_all
from repositories.base_repo import BaseRepository
from repositories.tables import RESOURCES, CrudResource


def _infer_field_meta(key: str):
    if key.lower() in {"diagnostico"}:
        return ("text", True)
    if "fecha" in key.lower():
        return ("date", False)
    if key.upper() in {"HI", "HF"} or "franja" in key.lower():
        return ("time", False)
    if "password" in key.lower():
        return ("password", False)
    if key.lower().endswith("id") or key.lower().startswith("id"):
        return ("number", False)
    if key.lower() in {"cedula", "edad", "cantidad", "estatura_cm"}:
        return ("number", False)
    if key.lower() in {"peso_kg"}:
        return ("number", False)
    return ("text", False)


def _create_crud_blueprint(
    resource: CrudResource,
    repo: BaseRepository,
):
    cfg = repo.cfg
    bp = Blueprint(resource.name, __name__, url_prefix=resource.url_prefix)

    @bp.get("/")
    def list_view():
        if resource.list_query:
            rows = fetch_all(current_app, resource.list_query)
            columns = resource.list_columns or (list(rows[0].keys()) if rows else [])
        else:
            rows = repo.list_all()
            columns = cfg.columns

        return render_template(
            "tabla.html",
            titulo=resource.title,
            columnas=columns,
            datos=rows,
            base_path=resource.url_prefix,
            pk_name=cfg.pk,
        )

    @bp.get("/new")
    def new_form():
        fields = [c for c in cfg.columns if c != cfg.pk]
        field_meta = {k: _infer_field_meta(k) for k in fields}
        return render_template(
            "crud_form.html",
            titulo=f"Nuevo - {resource.title}",
            base_path=resource.url_prefix,
            pk_name=cfg.pk,
            fields=fields,
            field_meta=field_meta,
            values={},
        )

    @bp.post("/new")
    def create_action():
        payload: Dict[str, Any] = {}
        for key in cfg.columns:
            if key == cfg.pk:
                continue
            payload[key] = request.form.get(key)
        new_id = repo.create(payload)
        flash(f"Creado correctamente ({cfg.pk}={new_id})", "success")
        return redirect(url_for(f"{resource.name}.list_view"))

    @bp.get("/<int:pk>/edit")
    def edit_form(pk: int):
        row = repo.get_by_id(pk)
        if not row:
            flash("Registro no encontrado", "danger")
            return redirect(url_for(f"{resource.name}.list_view"))

        fields = [c for c in cfg.columns if c != cfg.pk]
        field_meta = {k: _infer_field_meta(k) for k in fields}
        return render_template(
            "crud_form.html",
            titulo=f"Editar - {resource.title}",
            base_path=resource.url_prefix,
            pk_name=cfg.pk,
            pk_value=pk,
            fields=fields,
            field_meta=field_meta,
            values=row,
        )

    @bp.post("/<int:pk>/edit")
    def update_action(pk: int):
        payload: Dict[str, Any] = {}
        for key in cfg.columns:
            if key == cfg.pk:
                continue
            payload[key] = request.form.get(key)
        repo.update(pk, payload)
        flash("Actualizado correctamente", "success")
        return redirect(url_for(f"{resource.name}.list_view"))

    @bp.post("/<int:pk>/delete")
    def delete_action(pk: int):
        repo.delete(pk)
        flash("Eliminado correctamente", "success")
        return redirect(url_for(f"{resource.name}.list_view"))

    return bp


def register_crud_blueprints(app):
    for resource in RESOURCES.values():
        repo = BaseRepository(resource.table)
        bp = _create_crud_blueprint(resource, repo)
        app.register_blueprint(bp)

    return app
