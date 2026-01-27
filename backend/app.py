from pathlib import Path

from flask import Flask

from config import load_config
from routes.crud_routes import register_crud_blueprints
from routes.views import bp as views_bp


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
	app.register_blueprint(views_bp)
	register_crud_blueprints(app)

	return app


app = create_app()


if __name__ == "__main__":
	app.run(debug=True)

