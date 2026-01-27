from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from repositories.base_repo import TableConfig


@dataclass(frozen=True)
class CrudResource:
    name: str
    url_prefix: str
    title: str
    table: TableConfig
    # Optional overrides for the list page (useful for JOINs)
    list_columns: Optional[List[str]] = None
    list_query: Optional[str] = None


RESOURCES: Dict[str, CrudResource] = {
    "consultas": CrudResource(
        name="consultas",
        url_prefix="/consultas",
        title="Consultas",
        table=TableConfig(
            table="consultas",
            pk="IdConsulta",
            columns=[
                "IdConsulta",
                "IdMedico",
                "IdPaciente",
                "FechaConsulta",
                "HI",
                "HF",
                "Diagnostico",
            ],
            select_list_sql="IdConsulta, IdMedico, IdPaciente, FechaConsulta, HI, HF, Diagnostico",
            write_map={
                "IdMedico": "IdMedico",
                "IdPaciente": "IdPaciente",
                "FechaConsulta": "FechaConsulta",
                "HI": "HI",
                "HF": "HF",
                "Diagnostico": "Diagnostico",
            },
        ),
    ),
    "especialidades": CrudResource(
        name="especialidades",
        url_prefix="/especialidades",
        title="Especialidades",
        table=TableConfig(
            table="especialidades",
            pk="IdEsp",
            columns=["IdEsp", "Descripcion", "Dias", "Franja_HI", "Franja_HF"],
            select_list_sql="IdEsp, Descripcion, Dias, Franja_HI, Franja_HF",
            write_map={
                "Descripcion": "Descripcion",
                "Dias": "Dias",
                "Franja_HI": "Franja_HI",
                "Franja_HF": "Franja_HF",
            },
        ),
    ),
    "medicamentos": CrudResource(
        name="medicamentos",
        url_prefix="/medicamentos",
        title="Medicamentos",
        table=TableConfig(
            table="medicamentos",
            pk="IdMedicamento",
            columns=["IdMedicamento", "Nombre", "Tipo"],
            select_list_sql="IdMedicamento, Nombre, Tipo",
            write_map={
                "Nombre": "Nombre",
                "Tipo": "Tipo",
            },
        ),
    ),
    "medicos": CrudResource(
        name="medicos",
        url_prefix="/medicos",
        title="Medicos",
        table=TableConfig(
            table="medicos",
            pk="IdMedico",
            columns=["IdMedico", "Nombre", "Especialidad", "IdUsuario", "Foto"],
            select_list_sql="IdMedico, Nombre, Especialidad, IdUsuario, Foto",
            write_map={
                "Nombre": "Nombre",
                "Especialidad": "Especialidad",
                "IdUsuario": "IdUsuario",
                "Foto": "Foto",
            },
        ),
    ),
    "pacientes": CrudResource(
        name="pacientes",
        url_prefix="/pacientes",
        title="Pacientes",
        table=TableConfig(
            table="pacientes",
            pk="IdPaciente",
            columns=[
                "IdPaciente",
                "IdUsuario",
                "Nombre",
                "Cedula",
                "Edad",
                "Genero",
                "Estatura_cm",
                "Peso_kg",
                "Foto",
            ],
            select_list_sql=(
                "IdPaciente, IdUsuario, Nombre, Cedula, Edad, Genero, "
                "`Estatura (cm)` AS Estatura_cm, `Peso (kg)` AS Peso_kg, Foto"
            ),
            write_map={
                "IdUsuario": "IdUsuario",
                "Nombre": "Nombre",
                "Cedula": "Cedula",
                "Edad": "Edad",
                "Genero": "Genero",
                "Estatura_cm": "`Estatura (cm)`",
                "Peso_kg": "`Peso (kg)`",
                "Foto": "Foto",
            },
        ),
    ),
    "recetas": CrudResource(
        name="recetas",
        url_prefix="/recetas",
        title="Recetas",
        table=TableConfig(
            table="recetas",
            pk="IdReceta",
            columns=["IdReceta", "IdConsulta", "IdMedicamento", "Cantidad"],
            select_list_sql="IdReceta, IdConsulta, IdMedicamento, Cantidad",
            write_map={
                "IdConsulta": "IdConsulta",
                "IdMedicamento": "IdMedicamento",
                "Cantidad": "Cantidad",
            },
        ),
        list_columns=["IdReceta", "Consulta", "Medicamento", "Cantidad"],
        list_query=(
            "SELECT r.IdReceta, c.Diagnostico AS Consulta, m.Nombre AS Medicamento, r.Cantidad "
            "FROM recetas r "
            "JOIN consultas c ON r.IdConsulta = c.IdConsulta "
            "JOIN medicamentos m ON r.IdMedicamento = m.IdMedicamento "
            "ORDER BY r.IdReceta"
        ),
    ),
    "roles": CrudResource(
        name="roles",
        url_prefix="/roles",
        title="Roles",
        table=TableConfig(
            table="roles",
            pk="IdRol",
            columns=["IdRol", "Nombre", "Accion"],
            select_list_sql="IdRol, Nombre, Accion",
            write_map={
                "Nombre": "Nombre",
                "Accion": "Accion",
            },
        ),
    ),
    "usuarios": CrudResource(
        name="usuarios",
        url_prefix="/usuarios",
        title="Usuarios",
        table=TableConfig(
            table="usuarios",
            pk="IdUsuario",
            columns=["IdUsuario", "Nombre", "Password", "Rol"],
            select_list_sql="IdUsuario, Nombre, Password, Rol",
            write_map={
                "Nombre": "Nombre",
                "Password": "Password",
                "Rol": "Rol",
            },
        ),
    ),
}
