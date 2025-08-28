from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from . import bp
from ..extensions import db
from ..models import Cart, CartItem, CartItemSelection
from .logic import compute_priced_unit, PricingError

print(">>> app.cart.routes: imported")

def _load_or_create_cart(session_id: str | None, user_id: int | None):
    q = Cart.query.filter_by(status="active")
    cart = q.filter_by(user_id=user_id).first() if user_id else q.filter_by(session_id=session_id).first()

    if not cart:
        cart = Cart(user_id=user_id, session_id=session_id, status="active")
        db.session.add(cart)
        db.session.flush()  # obtain cart.id
    return cart

def _whoami():
    # Prefer JWT user if present; fall back to client-supplied session_id header
    try:
        uid = get_jwt_identity()
    except Exception:
        uid = None
    session_id = request.headers.get("X-Session-Id")  # e.g., UUID from frontend
    if not uid and not session_id:
        session_id = request.cookies.get("sid") or request.args.get("sid")
    return uid, session_id

@bp.get("/_ping")
def cart_ping():
    return {"ok": True}

@bp.get("")
def get_cart():
    uid, sid = _whoami()
    cart = _load_or_create_cart(sid, uid)
    db.session.commit()
    return jsonify(cart=cart.as_dict()), 200

@bp.post("/items")
def add_item():
    data = request.get_json(force=True) or {}
    product_id = int(data.get("product_id"))
    qty = max(1, int(data.get("quantity") or 1))
    selections = data.get("selections") or []

    uid, sid = _whoami()
    cart = _load_or_create_cart(sid, uid)

    try:
        unit_price, snaps = compute_priced_unit(product_id, selections)
    except PricingError as e:
        return jsonify(msg=str(e)), 400

    item = CartItem(
        cart_id=cart.id,
        product_id=product_id,
        quantity=qty,
        unit_price=unit_price,
        total_price=round(unit_price * qty, 2),
    )
    db.session.add(item)
    db.session.flush()

    for s in snaps:
        db.session.add(CartItemSelection(
            item_id=item.id,
            option_id=s["option_id"],
            option_value_id=s["option_value_id"],
            option_name=s["option_name"],
            value_label=s["value_label"],
            price_delta=s["price_delta"],
        ))

    db.session.commit()
    return jsonify(cart=cart.as_dict()), 201

@bp.patch("/items/<int:item_id>")
def update_item(item_id: int):
    item = CartItem.query.get_or_404(item_id)
    data = request.get_json(force=True) or {}
    qty = int(data.get("quantity") or item.quantity)
    if qty < 1:
        return jsonify(msg="quantity must be >= 1"), 400
    item.quantity = qty
    item.total_price = round(item.unit_price * item.quantity, 2)
    db.session.commit()
    return jsonify(cart=item.cart.as_dict()), 200

@bp.delete("/items/<int:item_id>")
def remove_item(item_id: int):
    item = CartItem.query.get_or_404(item_id)
    cart = item.cart
    db.session.delete(item)
    db.session.commit()
    return jsonify(cart=cart.as_dict()), 200

@bp.post("/checkout/preview")
def checkout_preview():
    uid, sid = _whoami()
    cart = _load_or_create_cart(sid, uid)
    return jsonify(subtotal=cart.subtotal()), 200
