# --- app/cart/logic.py ---
from ..models import Product, Option, OptionValue

class PricingError(ValueError):
    pass

def compute_priced_unit(product_id: int, selections_payload: list[dict]) -> tuple[float, list]:
    """
    selections_payload: [{"option_id": 1, "value_id": 4}, ...]
    Returns: (unit_price, selection_snapshots)
    """
    product = Product.query.get_or_404(product_id)

    # Map only this product's options
    options = Option.query.filter_by(product_id=product.id).all()
    option_by_id = {o.id: o for o in options}

    snapshots = []
    delta_sum = 0.0

    for sel in selections_payload or []:
        oid = int(sel["option_id"])
        vid = int(sel["value_id"])

        opt = option_by_id.get(oid)
        if not opt:
            raise PricingError(f"Option {oid} does not belong to product {product.id}")

        val = OptionValue.query.filter_by(id=vid, option_id=oid).first()
        if not val:
            raise PricingError(f"Value {vid} not found for option {oid}")

        # Use label/value safely
        label = getattr(val, "value", None) or getattr(val, "label", None) or getattr(val, "name", None)
        if label is None:
            raise PricingError(f"Option value {vid} missing label field")

        delta = float(getattr(val, "price_delta", 0.0) or 0.0)
        snapshots.append({
            "option_id": opt.id,
            "option_name": getattr(opt, "name", str(opt.id)),
            "option_value_id": val.id,         # ✅ val.id (not val.vid)
            "value_label": label,
            "price_delta": delta,
        })
        delta_sum += delta                   # ✅ add once

    unit_price = round(float(product.price) + delta_sum, 2)
    return unit_price, snapshots
