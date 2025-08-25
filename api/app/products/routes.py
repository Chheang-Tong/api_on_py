# --- app/products/routes.py ---
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from . import bp
from ..models import Product, ProductOptionGroup, ProductOptionValue
from ..extensions import db
from sqlalchemy import asc, desc

# ---------- Helpers -----------
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
    barcode = (data.get("barcode") or "").strip()
    name  = (data.get("name") or "").strip()
    price = _to_float(data.get("price"), 0.0)
    stock = _to_int(data.get("stock"), 0),
    
    if not name or not barcode:
        return jsonify(msg="name & barcode required"), 400
    if Product.query.filter_by(barcode=barcode).first():
        return jsonify(msg="barcode already exists"), 409
    p = Product(name=name,barcode=barcode, price=price, stock=stock)
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
      q            -> substring match on name; if q is an int, also match id
      barcode      -> exact barcode match (string)
      id           -> exact id match (int)
      ids          -> comma-separated ids, e.g. "1,3,9"
      min_price    -> float
      max_price    -> float
      in_stock     -> bool (true/false)
      sort         -> id, -id, name, -name, price, -price, stock, -stock
      page         -> int, default 1
      per_page     -> int, default 10 (cap 100)
    """
    q         = (request.args.get("q") or "").strip()
    barcode   = (request.args.get("barcode") or "").strip()
    id_param  = _to_int(request.args.get("id"))
    ids_param = request.args.get("ids")
    min_price = _to_float(request.args.get("min_price"))
    max_price = _to_float(request.args.get("max_price"))
    in_stock  = _to_bool(request.args.get("in_stock"))
    sort      = (request.args.get("sort") or "-id").strip()
    page      = max(_to_int(request.args.get("page"), 1), 1)
    per_page  = min(max(_to_int(request.args.get("per_page"), 10), 1), 100)

    qry = Product.query

    # --- Barcode filter ---
    if barcode:
        qry = qry.filter(Product.barcode.ilike(f"%{barcode}%"))

    # --- ID filters ---
    ids_list = None
    if ids_param:
        try:
            ids_list = [int(x) for x in ids_param.split(",") if x.strip().isdigit()]
        except ValueError:
            ids_list = []
    if id_param is not None:
        qry = qry.filter(Product.id == id_param)
    elif ids_list:
        qry = qry.filter(Product.id.in_(ids_list))
    else:
        if q:
            if q.isdigit():
                qry = qry.filter(
                    (Product.id == int(q)) | (Product.name.ilike(f"%{q}%"))
                )
            else:
                qry = qry.filter(Product.name.ilike(f"%{q}%"))

    # --- Price filters ---
    if min_price is not None:
        qry = qry.filter(Product.price >= min_price)
    if max_price is not None:
        qry = qry.filter(Product.price <= max_price)

    # --- Stock filter ---
    if in_stock is True:
        qry = qry.filter(Product.stock > 0)
    elif in_stock is False:
        qry = qry.filter(Product.stock == 0)

    #--- Name Filter ---
    # if q:
    #     if q.isdigit():
    #         qry = qry.filter(
    #             (Product.id == int(q)) | (Product.name.ilike(f"{q}%"))
    #         )
    #     else:
    #         qry = qry.filter(Product.name.ilike(f"{q}%"))


    # --- Sorting ---
    sort_map = {
        "id": Product.id, "-id": Product.id,
        "name": Product.name, "-name": Product.name,
        "price": Product.price, "-price": Product.price,
        "stock": Product.stock, "-stock": Product.stock,
    }
    col = sort_map.get(sort, Product.id)
    direction = desc if sort.startswith("-") else asc
    qry = qry.order_by(direction(col))

    # --- Pagination ---
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

# ---------- OPTION GROUPS ----------
@bp.post("/<int:pid>/option-groups")
@jwt_required()
def create_option_group(pid):
    """
    Create an option group for a product (e.g., Size, Color).
    Body:
    {
      "name": "Size",
      "required": true,
      "multiple": false
    }
    """
    product = Product.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    required = bool(data.get("required", False))
    multiple = bool(data.get("multiple", False))

    if not name:
        return jsonify(msg="group name required"), 400

    group = ProductOptionGroup(product=product, name=name, required=required, multiple=multiple)
    db.session.add(group)
    db.session.commit()

    return jsonify(group=group.as_option_payload()), 201


@bp.get("/<int:pid>/options")
@jwt_required()
def list_option_groups(pid):
    """
    Get all option groups (with values) for a product
    """
    product = Product.query.get_or_404(pid)
    return jsonify(options=[g.as_option_payload() for g in product.option_groups])


@bp.delete("/option-groups/<int:gid>")
@jwt_required()
def delete_option_group(gid):
    group = ProductOptionGroup.query.get_or_404(gid)
    db.session.delete(group)
    db.session.commit()
    return jsonify(deleted=True)


# ---------- OPTION VALUES ----------
@bp.post("/option-groups/<int:gid>/values")
@jwt_required()
def create_option_value(gid):
    """
    Add an option value to a group (e.g., S, M, L)
    Body:
    {
      "value": "L",
      "price_delta": 4,
      "is_default": false
    }
    """
    group = ProductOptionGroup.query.get_or_404(gid)
    data = request.get_json(silent=True) or {}
    value = (data.get("value") or "").strip()
    price_delta = _to_float(data.get("price_delta"), 0.0)
    is_default = bool(data.get("is_default", False))

    if not value:
        return jsonify(msg="value required"), 400

    # enforce only one default if group is single-choice
    if is_default and not group.multiple:
        for v in group.values:
            v.is_default = False

    val = ProductOptionValue(group=group, value=value, price_delta=price_delta, is_default=is_default)
    db.session.add(val)
    db.session.commit()

    return jsonify(value=val.as_value_payload()), 201


@bp.delete("/option-values/<int:vid>")
@jwt_required()
def delete_option_value(vid):
    val = ProductOptionValue.query.get_or_404(vid)
    db.session.delete(val)
    db.session.commit()
    return jsonify(deleted=True)