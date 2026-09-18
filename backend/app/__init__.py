from flask import Flask, jsonify
from pydantic import ValidationError

from app.database.db import database
from app.routes.auth.auth_route import auth_bp
from app.routes.links.link_route import link_bp
from app.utils.click_tracker import start_flush_loop
from app.utils.errors import AppError


def create_app() -> Flask:
    app = Flask(__name__)

    database.connect()
    database.init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(link_bp)

    start_flush_loop()

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        return response

    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify({"detail": e.message}), e.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({"detail": e.errors(include_context=False, include_url=False)}), 400

    return app
