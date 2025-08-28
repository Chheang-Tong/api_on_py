# --- products/routes.py ---
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_, asc, desc
from ..models import Product, Option, OptionValue
from ..extensions import db
from . import bp
import os
import json
from uuid import uuid4
from werkzeug.utils import secure_filename
from ..utils.decorators import require_headers
from ..utils.api import api_ok, api_error
import re

# ------------------------ config ------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# ------------------------ helpers ------------------------

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def _is_local_upload(url: str) -> bool:
    return isinstance(url, str) and url.startswith("/static/uploads/")

def _slugify(name: str) -> str:
    base = os.path.splitext(name)[0]
    s = re.sub(r'[^a-z0-9]+', '-', base.strip().lower())
    return s.strip('-') or 'image'

def save_upload(file_storage, custom_name=None):
    original = secure_filename(file_storage.filename or "")
    if not allowed_file(original):
        raise ValueError("unsupported image type or missing extension")

    ext = original.rsplit(".", 1)[1].lower()

    if custom_name:
        filename = secure_filename(custom_name) + "." + ext
    else:
        filename = original

    app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    upload_dir = os.path.join(app_root, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    full_path = os.path.join(upload_dir, filename)

    if os.path.exists(full_path):
        filename = f"{os.path.splitext(filename)[0]}-{uuid4().hex[:6]}.{ext}"
        full_path = os.path.join(upload_dir, filename)

    file_storage.save(full_path)

    return {
        "url": f"/static/uploads/{filename}",
        "name": filename
    }


def _remove_local_upload(url: str):
    # Only delete files inside app/static/uploads to avoid accidental deletions
    try:
        # /app/app/products -> /app/app
        app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        uploads_root = os.path.join(app_root, "static", "uploads")
        candidate = os.path.abspath(os.path.join(app_root, url.lstrip("/")))

        # safety: ensure candidate is inside uploads_root
        if os.path.commonpath([uploads_root, candidate]) == uploads_root and os.path.exists(candidate):
            os.remove(candidate)
    except Exception:
        # swallow cleanup errors to not break the request
        pass

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
@require_headers
@jwt_required()
def create_product():
    """
    Accepts:
      - multipart/form-data (recommended when uploading image)
        Fields: barcode, name, price, stock, category_id? + image file in "image"
      - OR application/json without a file; you can pass image_url directly
    """
    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    image_url = None
    options_payload = None
    if is_multipart:
        form = request.form
        barcode = (form.get("barcode") or "").strip()
        name    = (form.get("name") or "").strip()
        price   = float(form.get("price") or 0)
        stock   = int(form.get("stock") or 0)
        category_id = form.get("category_id")
        category_id = int(category_id) if category_id else None

        if form.get("options"):
            try:
                options_payload = json.loads(form.get("options"))
            except json.JSONDecodeError:
                return jsonify(api_error("invalid options JSON")), 400


        image_file = request.files.get("image")
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                return jsonify(msg="unsupported image type"), 400
            custom_from_form = (form.get("image_name") or "").strip() or None
            custom_name = custom_from_form or (_slugify(name) if name else None)
            saved= save_upload(image_file, custom_name=custom_name)
            image_url = saved["url"]
    else:
        data = request.get_json(silent=True) or {}
        barcode = (data.get("barcode") or "").strip()
        name = (data.get("name") or "").strip()
        price = _to_float(data.get("price"), 0.0)
        stock = _to_int(data.get("stock"), 0)
        category_id = _to_int(data.get("category_id"))
        image_url   = (data.get("image_url") or "").strip() or None
        options_payload = data.get("options")

    if not barcode :
        return jsonify(api_error("barcode required")), 400
    if not name:
        return jsonify(api_error("name required")), 400
    if Product.query.filter_by(barcode=barcode).first():
        return jsonify(api_error("barcode already exists")), 409

    product = Product(
        barcode=barcode,
        name=name,
        price=price,
        stock=stock,
        category_id=category_id,
        image_url=image_url,
    )
    db.session.add(product)

    # optional options payload
    if options_payload:
        _load_options_from_payload(product, options_payload)

    db.session.commit()
    return jsonify(
        # product=product.as_dict()
        api_ok(
            "Product created successfully",
            data={
                "product": product.as_dict(),
            }
        )), 201



# ------------------------ LIST ------------------------
@bp.get("/")
@require_headers
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
@require_headers
@jwt_required()
def get_product(pid):
    p = Product.query.get_or_404(pid)
    return jsonify(product=p.as_dict())


# ------------------------ UPDATE ------------------------
@bp.put("/<int:pid>")
@require_headers
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
@require_headers
@jwt_required()
def delete_product(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify(msg="deleted"), 200
# ------------------------ Update IMAGE ------------------------
@bp.post("/<int:pid>/image")
@require_headers
@jwt_required()

def upload_product_image(pid):
    p = Product.query.get_or_404(pid)
    old_url = p.image_url

    ct = (request.content_type or "").lower()

    new_url = None
    # 1) Support multipart file upload
    if "multipart/form-data" in ct:
        image_file = request.files.get("image")
        if not (image_file and image_file.filename):
            return jsonify(msg="no image provided"), 400
        if not allowed_file(image_file.filename):
            return jsonify(msg="unsupported image type"), 400
        custom_from_form = (request.form.get("image_name") or "").strip() or None
        fallback=_slugify(getattr(p, "name", "") or "")
        saved=save_upload(image_file, custom_name=custom_from_form or (fallback or None))
        new_url = saved['url']

    # 2) Or support JSON: {"image_url": "https://..."}
    elif "application/json" in ct:
        data = request.get_json(silent=True) or {}
        candidate_url = (data.get("image_url") or "").strip()
        if not candidate_url:
            return jsonify(msg="image_url required"), 400
        new_url = candidate_url

    else:
        return jsonify(msg="multipart/form-data or application/json required"), 400

    p.image_url = new_url
    db.session.commit()

    if old_url and _is_local_upload(old_url) and old_url != new_url:
        _remove_local_upload(old_url)

    return jsonify(product=p.as_dict()), 200