import os


class Config:
    """Configuración central del proyecto (puedes sobreescribir con variables de entorno)."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "123")
    DB_NAME = os.getenv("DB_NAME", "veris")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))


def load_config(app):
    app.config.from_object(Config)
    return app
