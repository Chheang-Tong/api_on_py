from flask import request, jsonify
from flask_jwt_extended import jwt_required
from . import bp
from ..models import Sale
from ..models import Product
from ..extensions import db
from app.utils.decorators import require_headers

@bp.post("/")
@require_headers
@jwt_required()
def create_sale():
    data = request.get_json(silent=True) or {}
    product_id = int(data.get("product_id") or 0)
    qty = int(data.get("qty") or 1)

    product = Product.query.get_or_404(product_id)
    if product.stock < qty:
        return jsonify(msg="not enough stock"), 400

    total = product.price * qty
    sale = Sale(product_id=product.id, qty=qty, total=total)

    product.stock -= qty
    db.session.add(sale)
    db.session.commit()

    return jsonify(sale={"id": sale.id, "product_id": product.id, "qty": qty, "total": total})

@bp.get("/")
@require_headers
@jwt_required()
def list_sales():
    sales = Sale.query.order_by(Sale.id.desc()).all()
    return jsonify(sales=[{"id": s.id, "product_id": s.product_id, "qty": s.qty, "total": s.total} for s in sales])
