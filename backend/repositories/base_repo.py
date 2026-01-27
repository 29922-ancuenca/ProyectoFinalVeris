from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from flask import current_app

from database.connection import execute, fetch_all, fetch_one


@dataclass(frozen=True)
class TableConfig:
    table: str
    pk: str
    # Column names exposed to templates/routes (safe keys)
    columns: List[str]
    # SQL fragment for SELECT list. Must alias to keys in `columns` when needed.
    select_list_sql: str
    # Map from exposed key -> DB column/expression for INSERT/UPDATE.
    write_map: Dict[str, str]

    @property
    def insert_keys(self) -> List[str]:
        return [c for c in self.columns if c != self.pk]


class BaseRepository:
    def __init__(self, cfg: TableConfig):
        self.cfg = cfg

    def list_all(self) -> List[Dict[str, Any]]:
        query = f"SELECT {self.cfg.select_list_sql} FROM {self.cfg.table}"
        return fetch_all(current_app, query)

    def get_by_id(self, pk_value: int) -> Optional[Dict[str, Any]]:
        query = f"SELECT {self.cfg.select_list_sql} FROM {self.cfg.table} WHERE {self.cfg.pk} = %s"
        return fetch_one(current_app, query, (pk_value,))

    def create(self, payload: Dict[str, Any]) -> int:
        keys = self.cfg.insert_keys
        db_columns = [self.cfg.write_map[k] for k in keys]
        placeholders = ", ".join(["%s"] * len(keys))
        query = f"INSERT INTO {self.cfg.table} ({', '.join(db_columns)}) VALUES ({placeholders})"
        params = tuple(payload.get(k) for k in keys)
        res = execute(current_app, query, params)
        return int(res["lastrowid"] or 0)

    def update(self, pk_value: int, payload: Dict[str, Any]) -> None:
        keys = self.cfg.insert_keys
        set_parts = [f"{self.cfg.write_map[k]} = %s" for k in keys]
        query = f"UPDATE {self.cfg.table} SET {', '.join(set_parts)} WHERE {self.cfg.pk} = %s"
        params = tuple(payload.get(k) for k in keys) + (pk_value,)
        execute(current_app, query, params)

    def delete(self, pk_value: int) -> None:
        query = f"DELETE FROM {self.cfg.table} WHERE {self.cfg.pk} = %s"
        execute(current_app, query, (pk_value,))
