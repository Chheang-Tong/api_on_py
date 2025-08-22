1) requirements.txt
flask==3.0.3
flask-cors==4.0.1
flask-sqlalchemy==3.1.1
flask-migrate==4.0.7
flask-jwt-extended==4.6.0
python-dotenv==1.0.1

2) app/init.py (app factory + blueprints)
from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt, cors
from .auth import bp as auth_bp
from .products import bp as products_bp
from .sales import bp as sales_bp

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    # register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(sales_bp, url_prefix="/api/sales")

    @app.get("/api/health")
    def health():
        return {"ok": True}

    return app

3) app/config.py
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///app.db"  # stored in instance/ by Flask when instance_relative_config=True
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

4) app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()

5) app/models/init.py (shared base models if needed)
from ..extensions import db
from datetime import datetime

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

6) app/auth/init.py
from flask import Blueprint
bp = Blueprint("auth", __name__)

from . import routes  # noqa

6.1) app/auth/models.py
from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def as_dict(self):
        return {"id": self.id, "email": self.email, "name": self.name}

6.2) app/auth/routes.py
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import bp
from .models import User
from ..extensions import db

@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()

    if not email or not password or not name:
        return jsonify(msg="email & password & name required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(msg="email already registered"), 409

    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user=user.as_dict()), 201

@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(msg="invalid credentials"), 401
    token = create_access_token(identity={"id": user.id, "email": user.email})
    return jsonify(access_token=token, user=user.as_dict())

@bp.get("/me")
@jwt_required()
def me():
    return jsonify(user=get_jwt_identity())

7) app/products/init.py
from flask import Blueprint
bp = Blueprint("products", __name__)
from . import routes  # noqa

7.1) app/products/models.py
from ..extensions import db
from ..models import TimestampMixin

class Product(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)

    def as_dict(self):
        return {"id": self.id, "name": self.name, "price": self.price, "stock": self.stock}

7.2) app/products/routes.py
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from . import bp
from .models import Product
from ..extensions import db

@bp.post("")
@jwt_required()
def create_product():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    price = data.get("price")
    stock = data.get("stock", 0)
    if not name or price is None:
        return jsonify(msg="name & price required"), 400
    p = Product(name=name, price=float(price), stock=int(stock))
    db.session.add(p)
    db.session.commit()
    return jsonify(product=p.as_dict()), 201

@bp.get("")
@jwt_required()
def list_products():
    items = Product.query.order_by(Product.id.desc()).all()
    return jsonify(products=[i.as_dict() for i in items])

@bp.get("/<int:pid>")
@jwt_required()
def get_product(pid):
    p = Product.query.get_or_404(pid)
    return jsonify(product=p.as_dict())

@bp.put("/<int:pid>")
@jwt_required()
def update_product(pid):
    p = Product.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}
    if "name" in data: p.name = (data["name"] or "").strip() or p.name
    if "price" in data: p.price = float(data["price"])
    if "stock" in data: p.stock = int(data["stock"])
    db.session.commit()
    return jsonify(product=p.as_dict())

@bp.delete("/<int:pid>")
@jwt_required()
def delete_product(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify(msg="deleted")

8) app/sales/init.py
from flask import Blueprint
bp = Blueprint("sales", __name__)
from . import routes  # noqa

8.1) app/sales/models.py
from ..extensions import db
from ..models import TimestampMixin

class Sale(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    product = db.relationship("Product", backref="sales")

8.2) app/sales/routes.py
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from . import bp
from .models import Sale
from ..products.models import Product
from ..extensions import db

@bp.post("")
@jwt_required()
def create_sale():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    qty = int(data.get("qty", 1))
    if not product_id or qty < 1:
        return jsonify(msg="product_id & qty required"), 400

    product = Product.query.get_or_404(product_id)
    if product.stock < qty:
        return jsonify(msg="insufficient stock"), 400

    sale = Sale(product_id=product.id, qty=qty, unit_price=product.price)
    product.stock -= qty
    db.session.add(sale)
    db.session.commit()
    return jsonify(sale={"id": sale.id, "product_id": product.id, "qty": sale.qty, "unit_price": sale.unit_price}), 201

@bp.get("")
@jwt_required()
def list_sales():
    items = Sale.query.order_by(Sale.id.desc()).all()
    rows = []
    for s in items:
        rows.append({
            "id": s.id,
            "product_id": s.product_id,
            "product_name": s.product.name if s.product else None,
            "qty": s.qty,
            "unit_price": s.unit_price,
            "total": s.qty * s.unit_price,
            "created_at": s.created_at.isoformat()
        })
    return jsonify(sales=rows)

9) wsgi.py (gunicorn entry)
from app import create_app
app = create_app()


Example gunicorn cmd: gunicorn -w 2 -b 0.0.0.0:8000 wsgi:app

10) README.md (quick start)
# my_api

## Setup
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# (optional) create .env with secrets
echo "SECRET_KEY=change-me
JWT_SECRET_KEY=change-me" > .env

## Initialize DB (SQLite)
export FLASK_APP='app:create_app'   # on Windows: set FLASK_APP=app:create_app
flask db init
flask db migrate -m "init"
flask db upgrade

## Run dev
flask --app app:create_app --debug run

# or via wsgi/gunicorn (prod-like)
gunicorn -w 2 -b 0.0.0.0:8000 wsgi:app

Sample requests (curl)