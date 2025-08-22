import os
from datetime import timedelta

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# ----------------------------------
# Config
# ----------------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # allow Flutter during dev

# SQLite file in current folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Use env var if set; else fallback (change in production!)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ----------------------------------
# Model
# ----------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {"id": self.id, "email": self.email}

# ----------------------------------
# DB init (create tables)
# ----------------------------------
with app.app_context():
    db.create_all()

# ----------------------------------
# Helpers
# ----------------------------------
def bad_request(msg, code=400):
    return jsonify({"success": False, "message": msg}), code

def ok(data=None):
    return jsonify({"success": True, "data": data or {}})

# ----------------------------------
# Routes
# ----------------------------------
@app.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return bad_request("email and password are required")

    if len(password) < 6:
        return bad_request("password must be at least 6 characters")

    if User.query.filter_by(email=email).first():
        return bad_request("email already registered", 409)

    user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    return ok({"user": user.to_dict()})

@app.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return bad_request("email and password are required")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return bad_request("invalid email or password", 401)

    token = create_access_token(identity=user.id)
    return ok({"access_token": token, "user": user.to_dict()})

@app.get("/auth/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return bad_request("user not found", 404)
    return ok({"user": user.to_dict()})

@app.get("/")
def root():
    return jsonify(message="Auth API is running")

# ----------------------------------
# Entry
# ----------------------------------
if __name__ == "__main__":
    app.run(port=5000)
