from flask import Flask
from .config import config
from .services.embed_service import EmbedService
from .services.vector_db_service import VectorDBService
from .routes import create_search_bp


def create_app(config_name=None):
    if config_name is None:
        config_name = "development"

    app = Flask(__name__)
    config_obj = config[config_name]
    app.config.from_object(config_obj)

    # Initialize services as local variables
    embed_service = EmbedService(config_obj)
    vector_db_service = VectorDBService(config_obj)

    # Register blueprints and pass services via closure
    app.register_blueprint(create_search_bp(embed_service, vector_db_service))

    # Health check route
    @app.route("/health")
    def health():
        return "", 200

    # Route for video ingest tasks
    @app.route("/tasks", methods=("GET", "POST"))
    def tasks():
        from flask import request, jsonify

        if request.method == "GET":
            data = {
                "tasks": [{"id": "1234"}],
            }
            return jsonify(data)
        else:
            data = {
                "id": "1234",
            }
            return jsonify(data), 201

    return app
