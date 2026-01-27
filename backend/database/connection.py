from __future__ import annotations

from contextlib import contextmanager

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
