from pathlib import Path

from flask import Flask

from config import load_config
from routes.crud_routes import bp as crud_bp


def create_app():
	root_dir = Path(__file__).resolve().parent.parent
	frontend_dir = root_dir / "frontend"
	app = Flask(
		__name__,
		template_folder=str(frontend_dir / "templates"),
		static_folder=str(frontend_dir / "static"),
		static_url_path="/static",
	)
	load_config(app)
	app.register_blueprint(crud_bp)

	return app


app = create_app()


if __name__ == "__main__":
	app.run(debug=True)

