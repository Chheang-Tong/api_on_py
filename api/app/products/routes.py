# --- products/routes.py ---
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_, asc, desc
from ..models import Product, Option, OptionValue
from ..extensions import db
from . import bp
# ------------------------ helpers ------------------------
def _to_int(v, default=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

def _to_float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

def _to_bool(v, default=None):
    if isinstance(v, bool):
        return v
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in ("1", "true", "t", "yes", "y"): return True
    if s in ("0", "false", "f", "no", "n"): return False
    return default

def _paginate(query, page, per_page):
    page = max(_to_int(page, 1), 1)
    per_page = min(max(_to_int(per_page, 10), 1), 100)
    items = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "meta": {
            "page": items.page,
            "pages": items.pages or 1,
            "per_page": per_page,
            "total": items.total,
        },
        "items": items.items,
    }

def _sort_products(query, sort):
    sort = (sort or "").strip()
    mapping = {
        "id": Product.id, "-id": desc(Product.id),
        "name": Product.name, "-name": desc(Product.name),
        "price": Product.price, "-price": desc(Product.price),
        "stock": Product.stock, "-stock": desc(Product.stock),
    }
    col = mapping.get(sort, desc(Product.id))  # default newest first
    return query.order_by(col)

def _load_options_from_payload(product, options_payload):
    """
    options_payload example:
    [
      {
        "name": "Size",
        "values": [
          {"unit": "S", "price_delta": -2},
          {"unit": "M", "price_delta": 2}
        ]
      }
    ]
    """
    created = []
    for og in options_payload or []:
        name = (og.get("name") or "").strip()
        if not name:
            continue
        opt = Option(name=name, product=product)
        for v in og.get("values") or []:
            val = OptionValue(
                unit=(v.get("unit") or None),
                price_delta=_to_float(v.get("price_delta"), 0.0),
                option=opt,
            )
            db.session.add(val)
        db.session.add(opt)
        created.append(opt)
    return created


# ------------------------ CREATE ------------------------
@bp.post("/")
@jwt_required()
def create_product():
    data = request.get_json(silent=True) or {}
    barcode = (data.get("barcode") or "").strip()
    name = (data.get("name") or "").strip()
    price = _to_float(data.get("price"), 0.0)
    stock = _to_int(data.get("stock"), 0)
    category_id = _to_int(data.get("category_id"))

    if not barcode or not name:
        return jsonify(msg="barcode & name required"), 400
    if Product.query.filter_by(barcode=barcode).first():
        return jsonify(msg="barcode already exists"), 409

    product = Product(
        barcode=barcode,
        name=name,
        price=price,
        stock=stock,
        category_id=category_id,
    )
    db.session.add(product)

    # optional options payload
    options_payload = data.get("options")
    if options_payload:
        _load_options_from_payload(product, options_payload)

    db.session.commit()
    return jsonify(product=product.as_dict()), 201


# ------------------------ LIST ------------------------
@bp.get("/")
@jwt_required()
def list_products():
    """
    Query params:
      q            -> substring match on name/barcode; if q is an int, also match id
      barcode      -> exact barcode match (string)
      id           -> exact id match (int)
      ids          -> comma-separated ids, e.g. "1,3,9"
      min_price    -> float
      max_price    -> float
      in_stock     -> bool (true/false)  (True = stock > 0, False = stock <= 0)
      category_id  -> int
      sort         -> id, -id, name, -name, price, -price, stock, -stock
      page         -> int, default 1
      per_page     -> int, default 10 (cap 100)
    """
    q = (request.args.get("q") or "").strip()
    barcode = (request.args.get("barcode") or "").strip()
    id_param = _to_int(request.args.get("id"))
    ids_param = (request.args.get("ids") or "").strip()
    min_price = _to_float(request.args.get("min_price"))
    max_price = _to_float(request.args.get("max_price"))
    in_stock = _to_bool(request.args.get("in_stock"))
    category_id = _to_int(request.args.get("category_id"))
    sort = request.args.get("sort")
    page = request.args.get("page")
    per_page = request.args.get("per_page")

    query = Product.query

    if q:
        maybe_id = _to_int(q)
        like = f"%{q}%"
        query = query.filter(
            or_(
                Product.name.ilike(like),
                Product.barcode.ilike(like),
                Product.id == maybe_id if maybe_id is not None else False,
            )
        )

    if barcode:
        query = query.filter(Product.barcode == barcode)

    if id_param is not None:
        query = query.filter(Product.id == id_param)

    if ids_param:
        try:
            ids_list = [int(x.strip()) for x in ids_param.split(",") if x.strip()]
            if ids_list:
                query = query.filter(Product.id.in_(ids_list))
        except ValueError:
            return jsonify(msg="ids must be comma-separated integers"), 400

    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if in_stock is True:
        query = query.filter(Product.stock > 0)
    elif in_stock is False:
        query = query.filter(Product.stock <= 0)

    if category_id is not None:
        query = query.filter(Product.category_id == category_id)

    query = _sort_products(query, sort)
    page_data = _paginate(query, page, per_page)

    return jsonify(
        meta=page_data["meta"],
        products=[p.as_dict() for p in page_data["items"]],
    )


# ------------------------ READ ONE ------------------------
@bp.get("/<int:pid>")
@jwt_required()
def get_product(pid):
    p = Product.query.get_or_404(pid)
    return jsonify(product=p.as_dict())


# ------------------------ UPDATE ------------------------
@bp.put("/<int:pid>")
@jwt_required()
def update_product(pid):
    p = Product.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}

    if "barcode" in data:
        new_barcode = (data.get("barcode") or "").strip()
        if not new_barcode:
            return jsonify(msg="barcode cannot be empty"), 400
        exists = Product.query.filter(Product.barcode == new_barcode, Product.id != p.id).first()
        if exists:
            return jsonify(msg="barcode already exists"), 409
        p.barcode = new_barcode

    if "name" in data:
        new_name = (data.get("name") or "").strip()
        if not new_name:
            return jsonify(msg="name cannot be empty"), 400
        p.name = new_name

    if "price" in data:
        p.price = _to_float(data.get("price"), p.price)
    if "stock" in data:
        p.stock = _to_int(data.get("stock"), p.stock)
    if "category_id" in data:
        p.category_id = _to_int(data.get("category_id"))

    # Replace ALL options if "options" key is present (full overwrite)
    if "options" in data:
        # delete existing (orphan removal via cascade)
        for opt in list(p.options):
            db.session.delete(opt)
        _load_options_from_payload(p, data.get("options"))

    db.session.commit()
    return jsonify(product=p.as_dict())


# ------------------------ DELETE ------------------------
@bp.delete("/<int:pid>")
@jwt_required()
def delete_product(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify(msg="deleted"), 200
