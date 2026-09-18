from flask import Blueprint, request, jsonify

from app.routes.auth.auth_service import generate_user_api_key, signup_user, login_user
from app.routes.auth.schemas import SignupRequest, LoginRequest
from app.utils.current_user import get_current_user_id

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/signup")
def signup():
    data = SignupRequest(**request.get_json(force=True))
    result = signup_user(data)
    return jsonify(result), 201


@auth_bp.post("/login")
def login():
    data = LoginRequest(**request.get_json(force=True))
    result = login_user(data)
    return jsonify(result), 200


@auth_bp.post("/api-key")
def create_api_key():
    user_id = get_current_user_id()
    result = generate_user_api_key(user_id)
    return jsonify(result), 201
