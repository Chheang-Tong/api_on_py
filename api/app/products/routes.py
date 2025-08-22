from flask import request, jsonify
from flask_jwt_extended import jwt_required
from . import bp
from .models import Product
from ..extensions import db
from sqlalchemy import asc, desc

# ---------- Helpers ----------
def _to_bool(val, default=None):
    if val is None:
        return default
    s = str(val).strip().lower()
    if s in {"1","true","t","yes","y"}: return True
    if s in {"0","false","f","no","n"}: return False
    return default

def _to_float(val, default=None):
    try: return float(val)
    except (TypeError, ValueError): return default

def _to_int(val, default=None):
    try: return int(val)
    except (TypeError, ValueError): return default


# ---------- CREATE ----------
@bp.post("/")
@jwt_required()
def create_product():
    data = request.get_json(silent=True) or {}
    name  = (data.get("name") or "").strip()
    price = _to_float(data.get("price"), 0.0)
    stock = _to_int(data.get("stock"), 0)
    if not name:
        return jsonify(msg="name required"), 400
    p = Product(name=name, price=price, stock=stock)
    db.session.add(p)
    db.session.commit()
    return jsonify(product=p.as_dict()), 201


# ---------- DETAIL ----------
@bp.get("/<int:pid>")
@jwt_required()
def get_product(pid):
    p = Product.query.get_or_404(pid)
    return jsonify(product=p.as_dict())


# ---------- LIST + FILTERS ----------
@bp.get("/")
@jwt_required()
def list_products():
    """
    Query params:
      q            -> substring match on name
      min_price    -> float
      max_price    -> float
      in_stock     -> bool (true/false) -> stock > 0 if true, == 0 if false
      sort         -> one of: id, -id, name, -name, price, -price, stock, -stock
      page         -> int, default 1
      per_page     -> int, default 10 (cap at 100)
    """
    q         = (request.args.get("q") or "").strip()
    min_price = _to_float(request.args.get("min_price"))
    max_price = _to_float(request.args.get("max_price"))
    in_stock  = _to_bool(request.args.get("in_stock"))
    sort      = (request.args.get("sort") or "-id").strip()
    page      = max(_to_int(request.args.get("page"), 1), 1)
    per_page  = min(max(_to_int(request.args.get("per_page"), 10), 1), 100)

    qry = Product.query

    if q:
        qry = qry.filter(Product.name.ilike(f"%{q}%"))

    if min_price is not None:
        qry = qry.filter(Product.price >= min_price)

    if max_price is not None:
        qry = qry.filter(Product.price <= max_price)

    if in_stock is True:
        qry = qry.filter(Product.stock > 0)
    elif in_stock is False:
        qry = qry.filter(Product.stock == 0)

    # Sorting
    sort_map = {
        "id": Product.id, "-id": Product.id,
        "name": Product.name, "-name": Product.name,
        "price": Product.price, "-price": Product.price,
        "stock": Product.stock, "-stock": Product.stock,
    }
    col = sort_map.get(sort, Product.id)
    direction = desc if sort.startswith("-") else asc
    qry = qry.order_by(direction(col))

    # Pagination
    page_obj = qry.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        products=[p.as_dict() for p in page_obj.items],
        meta={
            "page": page_obj.page,
            "per_page": page_obj.per_page,
            "total": page_obj.total,
            "pages": page_obj.pages
        }
    )


# ---------- UPDATE ----------
@bp.put("/<int:pid>")
@jwt_required()
def update_product(pid):
    p = Product.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}
    if "name" in data:  p.name  = (data["name"] or "").strip()
    if "price" in data: p.price = _to_float(data["price"], p.price)
    if "stock" in data: p.stock = _to_int(data["stock"], p.stock)
    db.session.commit()
    return jsonify(product=p.as_dict())


# ---------- DELETE ----------
@bp.delete("/<int:pid>")
@jwt_required()
def delete_product(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify(deleted=True)
