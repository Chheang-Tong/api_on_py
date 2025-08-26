# --- models/product.py ---
from ..extensions import db

# ---------------- PRODUCT ----------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(180), nullable=False, unique=True)
    name = db.Column(db.String(180), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)

    options = db.relationship(
        "Option",
        backref="product",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def as_dict(self):
        return {
            "id": self.id,
            "barcode": self.barcode,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "category": self.category.as_dict() if self.category else None,
            "options": [o.as_dict() for o in self.options],
        }
        

