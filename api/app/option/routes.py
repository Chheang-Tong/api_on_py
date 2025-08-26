# --- options/routes.py ---
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_, asc, desc
from ..models import Product, Option, OptionValue
from ..extensions import db
from . import bp
# ------------------------ helpers ------------------------
def _to_float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

# ------------------------ OPTIONS: create option ------------------------
@bp.post("/")
@jwt_required()
def add_option(pid):
    p = Option.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(msg="option name required"), 400

    opt = Option(name=name, product=p)
    for v in data.get("values") or []:
        opt.values.append(
            OptionValue(
                unit=(v.get("unit") or None),
                price_delta=_to_float(v.get("price_delta"), 0.0),
            )
        )
    db.session.add(opt)
    db.session.commit()
    return jsonify(option=opt.as_dict(), product=p.as_dict()), 201


# ------------------------ OPTIONS: update/delete ------------------------
@bp.put("/<int:oid>")
@jwt_required()
def update_option(oid):
    opt = Option.query.get_or_404(oid)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify(msg="option name cannot be empty"), 400
        opt.name = name

    if "values" in data:
        for v in list(opt.values):
            db.session.delete(v)
        for v in data.get("values") or []:
            db.session.add(
                OptionValue(
                    option=opt,
                    unit=(v.get("unit") or None),
                    price_delta=_to_float(v.get("price_delta"), 0.0),
                )
            )

    db.session.commit()
    return jsonify(option=opt.as_dict())


@bp.delete("/<int:oid>")
@jwt_required()
def delete_option(oid):
    opt = Option.query.get_or_404(oid)
    db.session.delete(opt)
    db.session.commit()
    return jsonify(msg="deleted"), 200


# ------------------------ OPTION VALUES: create on option ------------------------
@bp.post("/<int:oid>/values")
@jwt_required()
def add_option_value(oid):
    opt = Option.query.get_or_404(oid)
    data = request.get_json(silent=True) or {}

    val = OptionValue(
        option=opt,
        unit=(data.get("unit") or None),
        price_delta=_to_float(data.get("price_delta"), 0.0),
    )
    db.session.add(val)
    db.session.commit()
    return jsonify(value=val.as_dict(), option=opt.as_dict()), 201


# ------------------------ OPTION VALUES: update/delete ------------------------
@bp.put("/values/<int:vid>")
@jwt_required()
def update_option_value(vid):
    val = OptionValue.query.get_or_404(vid)
    data = request.get_json(silent=True) or {}
    if "unit" in data:
        val.unit = (data.get("unit") or None)
    if "price_delta" in data:
        val.price_delta = _to_float(data.get("price_delta"), val.price_delta)
    db.session.commit()
    return jsonify(value=val.as_dict())


@bp.delete("/values/<int:vid>")
@jwt_required()
def delete_option_value(vid):
    val = OptionValue.query.get_or_404(vid)
    db.session.delete(val)
    db.session.commit()
    return jsonify(msg="deleted"), 200





# from flask import Blueprint, request, jsonify
# from flask_jwt_extended import jwt_required
# from ..models import Product, Option, OptionValue   # <-- include Product
# from ..extensions import db

# bp = Blueprint("options", __name__, url_prefix="/api/options")

# def _to_float(v, default=None):
#     try: return float(v)
#     except (TypeError, ValueError): return default

# # Create an option on a product
# @bp.post("/<int:pid>")
# @jwt_required()
# def add_option(pid):
#     p = Product.query.get_or_404(pid)   # <-- fix: look up Product
#     data = request.get_json(silent=True) or {}
#     name = (data.get("name") or "").strip()
#     if not name:
#         return jsonify(msg="option name required"), 400

#     opt = Option(name=name, product=p)
#     for v in data.get("values") or []:
#         opt.values.append(
#             OptionValue(
#                 unit=(v.get("unit") or None),
#                 price_delta=_to_float(v.get("price_delta"), 0.0),
#             )
#         )
#     db.session.add(opt)
#     db.session.commit()
#     return jsonify(option=opt.as_dict(), product=p.as_dict()), 201

# @bp.put("/<int:oid>")
# @jwt_required()
# def update_option(oid):
#     opt = Option.query.get_or_404(oid)
#     data = request.get_json(silent=True) or {}
#     if "name" in data:
#         name = (data.get("name") or "").strip()
#         if not name:
#             return jsonify(msg="option name cannot be empty"), 400
#         opt.name = name
#     if "values" in data:
#         for v in list(opt.values):
#             db.session.delete(v)
#         for v in data.get("values") or []:
#             db.session.add(
#                 OptionValue(
#                     option=opt,
#                     unit=(v.get("unit") or None),
#                     price_delta=_to_float(v.get("price_delta"), 0.0),
#                 )
#             )
#     db.session.commit()
#     return jsonify(option=opt.as_dict()))

# @bp.delete("/<int:oid>")
# @jwt_required()
# def delete_option(oid):
#     opt = Option.query.get_or_404(oid)
#     db.session.delete(opt)
#     db.session.commit()
#     return jsonify(msg="deleted"), 200

# @bp.post("/<int:oid>/values")
# @jwt_required()
# def add_option_value(oid):
#     opt = Option.query.get_or_404(oid)
#     data = request.get_json(silent=True) or {}
#     val = OptionValue(
#         option=opt,
#         unit=(data.get("unit") or None),
#         price_delta=_to_float(data.get("price_delta"), 0.0),
#     )
#     db.session.add(val)
#     db.session.commit()
#     return jsonify(value=val.as_dict(), option=opt.as_dict()), 201

# @bp.put("/values/<int:vid>")
# @jwt_required()
# def update_option_value(vid):
#     val = OptionValue.query.get_or_404(vid)
#     data = request.get_json(silent=True) or {}
#     if "unit" in data:
#         val.unit = (data.get("unit") or None)
#     if "price_delta" in data:
#         # keep current if parsing fails
#         parsed = _to_float(data.get("price_delta"), val.price_delta)
#         val.price_delta = parsed if parsed is not None else val.price_delta
#     db.session.commit()
#     return jsonify(value=val.as_dict()))

# @bp.delete("/values/<int:vid>")
# @jwt_required()
# def delete_option_value(vid):
#     val = OptionValue.query.get_or_404(vid)
#     db.session.delete(val)
#     db.session.commit()
#     return jsonify(msg="deleted"), 200
