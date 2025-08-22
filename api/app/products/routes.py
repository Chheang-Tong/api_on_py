from flask import request, jsonify
from flask_jwt_extended import jwt_required
from . import bp
from .models import Product
from ..extensions import db

@bp.post("/")
@jwt_required()
def create_product():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    price = float(data.get("price") or 0)
    stock = int(data.get("stock") or 0)
    if not name:
        return jsonify(msg="name required"), 400
    p = Product(name=name, price=price, stock=stock)
    db.session.add(p)
    db.session.commit()
    return jsonify(product=p.as_dict()), 201

@bp.get("/")
@jwt_required()
def list_products():
    items = Product.query.order_by(Product.id.desc()).all()
    return jsonify(products=[p.as_dict() for p in items])

@bp.put("/<int:pid>")
@jwt_required()
def update_product(pid):
    p = Product.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}
    if "name" in data:  p.name = data["name"]
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
    return jsonify(deleted=True)
