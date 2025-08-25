from datetime import datetime
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from . import bp
from app.auth.models import User
from ..extensions import db
from ..utils.net import get_client_ip, parse_coord, clamp_lat_lng

@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # optional lat/lng from client
    lat = parse_coord(data.get("lat"))
    lng = parse_coord(data.get("lng"))
    lat, lng = clamp_lat_lng(lat, lng)

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(msg="invalid credentials"), 401

    # record login metadata
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = get_client_ip()
    # only update coords if client sent valid ones (don’t overwrite with None)
    if lat is not None and lng is not None:
        user.last_login_lat = lat
        user.last_login_lng = lng

    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify(
        access_token=token,
        user=user.as_dict()
    ), 200
