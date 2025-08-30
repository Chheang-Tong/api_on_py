from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,create_refresh_token
from datetime import datetime, timedelta
from . import bp 
from ..models import User,RefreshToken
from ..extensions import db 
from ..utils.net import get_client_ip, parse_coord, clamp_lat_lng
from ..utils.api import api_ok, api_error
import uuid



# ---- Enforce headers for this blueprint ----
@bp.before_request
def require_headers():
   if request.endpoint and request.endpoint.endswith('.get_headers'):
        return
   if not request.is_json:
       return jsonify(msg="Content-Type must be application/json"), 415
   
   platform = request.headers.get("Platform")
   lang = request.headers.get("Accept-Language")
   sub_key = request.headers.get("Ocp-Apim-Subscription-Key")

   if not platform or not lang or not sub_key:
       return jsonify(msg="Missing required headers"), 400
   
   expected = current_app.config.get("APIM_SUBSCRIPTION_KEY")
   if expected and sub_key != expected:
       return jsonify(msg="Invalid Ocp-Apim-Subscription-Key"), 401

@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name =(data.get("name")or"").strip()

    if not email :
        return jsonify(msg="email required"), 400
    if not password or len(password) < 6:
        return jsonify(msg="password required, min 6 chars"), 400
    if not name:
        return jsonify(msg="name required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(msg="email already registered"), 409

    user = User(
        email=email, 
        password_hash=generate_password_hash(password),
        name=name
        )
    db.session.add(user)
    db.session.commit()
    
    return jsonify(api_ok(
        "Account created successfully",
        data={
            "user": user.as_dict(),
            "user_logged_in": True,
        })), 201

@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not email or not password:
        return jsonify(api_error("Email and password are required")), 400
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(api_error("Invalid email or password")), 401
    # token = create_access_token(identity=str(user.id))

    access_token = create_access_token(identity=str(user.id))

    token_str = str(uuid.uuid4())
    refresh = RefreshToken(
        user_id=user.id,
        token=token_str,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(refresh)
    db.session.commit()

    return jsonify(api_ok(
        "You've logged in successfully",
        data={
            "user": user.as_dict(),
            "user_logged_in": True,
            "token": access_token,
            "refresh_token": token_str
        }
    )), 200
    
@bp.get("/me")
@jwt_required()
def me_alias():
    uid = get_jwt_identity()  
    user = User.query.get(int(uid))
    if not user:
        return jsonify(api_error("user not found")), 404
    return jsonify(user=user.as_dict())

@bp.get("/headers")
def get_headers():
    headers = {
        "Content-Type": request.headers.get("Content-Type"),
        "Accept": request.headers.get("Accept"),
        "Platform": request.headers.get("Platform"),
        "Accept-Language": request.headers.get("Accept-Language"),
        "Ocp-Apim-Subscription-Key": request.headers.get("Ocp-Apim-Subscription-Key"),
    }
    return jsonify(headers)

@bp.post("/refresh")

def refresh():
    data = request.get_json() or {}
    token_str = data.get("refresh_token")
    refresh = RefreshToken.query.filter_by(token=token_str).first()
    if not refresh or refresh.expires_at < datetime.utcnow():
        return jsonify(api_error("Invalid or expired refresh token")), 401

    # issue new access token
    new_access = create_access_token(identity=str(refresh.user_id), expires_delta=timedelta(days=1))
    return jsonify(accessToken=new_access), 200
