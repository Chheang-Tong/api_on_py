====> Modular <=====
my_api/
├─ app/
│  ├─ __init__.py          # app factory, db, jwt, CORS, blueprints
│  ├─ config.py            # configuration
│  ├─ extensions.py        # db, jwt, migrate, cors instances
│  ├─ models/              # shared SQLAlchemy models (if any)
│  │  └─ __init__.py
│  ├─ auth/                # login/register feature
│  │  ├─ __init__.py
│  │  ├─ routes.py
│  │  └─ models.py
│  ├─ products/            # product CRUD feature
│  │  ├─ __init__.py
│  │  ├─ routes.py
│  │  └─ models.py
│  └─ sales/               # create sale, list sales
│     ├─ __init__.py
│     ├─ routes.py
│     └─ models.py
├─ instance/               # runtime stuff (not in git)
│  └─ app.db               # SQLite database file
├─ wsgi.py                 # entrypoint for gunicorn/production
├─ requirements.txt
└─ README.md

====> How to run (dev) <====
----------------------------
cd my_api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# first run
python wsgi.py
# -> Running on http://127.0.0.1:5000
 ====> A. make venv & folder <====

source "/Users/davidlong/Desktop/for learn/api/.venv/bin/activate"
cd "/Users/davidlong/Desktop/for learn/api"
which python
which pip

====> B. install flask and friends (inside the venv) <====
pip install --upgrade pip
pip install flask flask_sqlalchemy flask_jwt_extended flask_cors
which flask


====> if fail <=====
which python
python -V
which pip
pip -V
which flask

=====> Quick Sanity <====
pwd
ls -la
cat wsgi.py
python - <<'PY'
from app import create_app
app = create_app()
print('App name:', app.name)
print('Blueprints:', list(app.blueprints.keys()))
PY
------------------------

# From the api folder
python - <<'PY'
from app import create_app
print('Factory OK:', create_app)
app = create_app()
print('App name:', app.name)
print('Blueprints:', list(app.blueprints.keys()))
PY

FLASK_APP=app:create_app flask routes

==============================
1) Make a minimal app/__init__.py
cat > app/__init__.py <<'PY'
import os
from flask import Flask, jsonify
from .extensions import db, jwt, cors

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # DB in instance/app.db
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, "app.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")

    # init extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    # register blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    @app.get("/")
    def health():
        return jsonify(ok=True, msg="API running")

    # dev: create tables
    with app.app_context():
        db.create_all()

    return app
PY

2) app/extensions.py
cat > app/extensions.py <<'PY'
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
PY

3) app/auth/__init__.py
mkdir -p app/auth
cat > app/auth/__init__.py <<'PY'
from flask import Blueprint
bp = Blueprint("auth", __name__)
from . import routes  # keep this import so routes register
PY

4) app/auth/models.py
cat > app/auth/models.py <<'PY'
from ..extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    def as_dict(self):
        return {"id": self.id, "email": self.email}
PY

5) app/auth/routes.py
cat > app/auth/routes.py <<'PY'
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
    if not email or not password:
        return jsonify(msg="email & password required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(msg="email already registered"), 409

    user = User(email=email, password_hash=generate_password_hash(password))
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
    token = create_access_token(identity=user.id)
    return jsonify(access_token=token, user=user.as_dict())

@bp.get("/me")
@jwt_required()
def me():
    uid = get_jwt_identity()
    user = User.query.get(uid)
    if not user:
        return jsonify(msg="user not found"), 404
    return jsonify(user=user.as_dict())
PY

6) wsgi.py
cat > wsgi.py <<'PY'
from app import create_app
app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
PY

=====> Remove db <=====
rm instance/app.db

==========
pip install flask-migrate alembic
latlng

