from flask import Blueprint, jsonify, redirect, request

from app.core.config import SHORTEN_RATE_LIMIT_PER_MINUTE
from app.routes.links.link_service import (
    create_short_link,
    delete_link,
    get_link_stats,
    get_top_links,
    get_user_links,
    resolve_link,
)
from app.routes.links.schemas import ShortenRequest
from app.utils.current_user import get_authenticated_user_id, get_current_user_id
from app.utils.rate_limit import enforce_rate_limit

link_bp = Blueprint("links", __name__)


@link_bp.post("/shorten")
def shorten():
    enforce_rate_limit("shorten", SHORTEN_RATE_LIMIT_PER_MINUTE)
    owner_id = get_current_user_id()
    data = ShortenRequest(**request.get_json(force=True))
    result = create_short_link(data, owner_id)
    return jsonify(result), 201


@link_bp.get("/stats/<code>")
def stats(code):
    result = get_link_stats(code)
    return jsonify(result), 200


@link_bp.get("/analytics")
def analytics():
    return jsonify(get_top_links(5)), 200


@link_bp.get("/my-links")
def my_links():
    owner_id = get_current_user_id()
    return jsonify(get_user_links(owner_id)), 200


@link_bp.get("/<code>")
def redirect_to_original(code):
    original_url = resolve_link(code)
    return redirect(original_url)


@link_bp.delete("/<code>")
def delete(code):
    owner_id = get_authenticated_user_id()
    delete_link(code, owner_id)
    return "", 204
