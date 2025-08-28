from datetime import datetime
from sqlalchemy import CheckConstraint, event
from ..extensions import db

class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    # allow null & remove unique=True so a user can have multiple carts over time; you keep just one "active"
    user_id = db.Column(db.Integer, nullable=True, index=True)
    session_id = db.Column(db.String(180), nullable=True, index=True)
    status = db.Column(db.String(50), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    items = db.relationship(
        "CartItem",
        backref="cart",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def subtotal(self):
        return round(sum(i.total_price for i in (self.items or [])), 2)

    def as_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "status": self.status,
            "items": [i.as_dict() for i in (self.items or [])],
            "subtotal": self.subtotal(),
        }

class CartItem(db.Model):
    __tablename__ = "cart_item"
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    total_price = db.Column(db.Float, nullable=False, default=0.0)

    product = db.relationship("Product", lazy="joined")
    selections = db.relationship(
        "CartItemSelection",
        backref="item",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_cart_item_qty_pos"),
    )

    def recalc_totals(self):
        delta = sum(s.price_delta for s in (self.selections or []))
        base = self.product.price if self.product else 0.0
        self.unit_price = float(base) + float(delta)
        self.total_price = round(self.unit_price * self.quantity, 2)

    def as_dict(self):
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "product": {
                "id": self.product.id if self.product else None,
                "name": self.product.name if self.product else None,
                "price": self.product.price if self.product else 0.0,
                "image_url": getattr(self.product, "image_url", None),
            },
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "selections": [s.as_dict() for s in (self.selections or [])],
        }

@event.listens_for(CartItem, "before_insert")
@event.listens_for(CartItem, "before_update")
def _cartitem_totals(_mapper, _conn, target: CartItem):
    target.recalc_totals()

class CartItemSelection(db.Model):
    __tablename__ = "cart_item_selection"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("cart_item.id"), nullable=False, index=True)
    option_id = db.Column(db.Integer, db.ForeignKey("option.id"), nullable=False, index=True)
    option_value_id = db.Column(db.Integer, db.ForeignKey("option_value.id"), nullable=False, index=True)
    option_name = db.Column(db.String(120), nullable=False)
    value_label = db.Column(db.String(120), nullable=False)
    price_delta = db.Column(db.Float, nullable=False, default=0.0)

    def as_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "option_id": self.option_id,
            "option_value_id": self.option_value_id,
            "option_name": self.option_name,
            "value": self.value_label,
            "price_delta": self.price_delta,
        }
