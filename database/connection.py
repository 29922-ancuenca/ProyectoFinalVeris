from __future__ import annotations

from contextlib import contextmanager

from typing import Any, Dict, List, Optional, cast

import mysql.connector


@contextmanager
def get_connection(app=None):
    """Context manager para conexión MySQL.

    Lee credenciales desde app.config si se provee `app`.
    """

    if app is None:
        raise RuntimeError("Se requiere `app` para leer config de DB")

    conn = mysql.connector.connect(
        host=app.config["DB_HOST"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        database=app.config["DB_NAME"],
        port=app.config.get("DB_PORT", 3306),
    )

    try:
        yield conn
    finally:
        conn.close()


def fetch_all(app, query: str, params: tuple | None = None) -> List[Dict[str, Any]]:
    with get_connection(app) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        rows = cur.fetchall() or []
        cur.close()
        return cast(List[Dict[str, Any]], rows)


def fetch_one(app, query: str, params: tuple | None = None) -> Optional[Dict[str, Any]]:
    with get_connection(app) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        row = cur.fetchone()
        cur.close()
        return cast(Optional[Dict[str, Any]], row)


def execute(app, query: str, params: tuple | None = None):
    with get_connection(app) as conn:
        cur = conn.cursor()
        cur.execute(query, params or ())
        conn.commit()
        lastrowid = getattr(cur, "lastrowid", None)
        rowcount = getattr(cur, "rowcount", None)
        cur.close()
        return {"lastrowid": lastrowid, "rowcount": rowcount}
