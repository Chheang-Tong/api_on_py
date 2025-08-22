from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from . import bp
from .models import User
from ..extensions import db

@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name =(data.get("name")or"").strip()

    if not email or not password or not name:
        return jsonify(msg="email & password & name required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(msg="email already registered"), 409

    user = User(
        email=email, 
        password_hash=generate_password_hash(password),
        name=name
        )
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user=user.as_dict()), 201

@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(msg="invalid credentials"), 401
    # token = create_access_token(identity=user.id)
    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token, user=user.as_dict())
    
# @bp.get("/me")
# @jwt_required()
# def me_alias():
#     # uid = get_jwt_identity()
#     uid = int(get_jwt_identity())
#     user = User.query.get(uid)
#     if not user:
#         return jsonify(msg="user not found"), 404
#     return jsonify(user=user.as_dict())

@bp.get("/me")
@jwt_required()
def me_alias():
    uid = get_jwt_identity()  
    user = User.query.get(int(uid))
    if not user:
        return jsonify(msg="user not found"), 404
    return jsonify(user=user.as_dict())

