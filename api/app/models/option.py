# --- models/option.py ---
from ..extensions import db

# ---------------- OPTION ----------------
class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    values = db.relationship(
        "OptionValue",
        backref="option",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "values": [v.as_dict() for v in self.values],
        }


# ---------------- OPTION VALUE ----------------
class OptionValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price_delta = db.Column(db.Float, nullable=False, default=0.0)
    unit = db.Column(db.String(50), nullable=True) 

    option_id = db.Column(db.Integer, db.ForeignKey("option.id"), nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "unit": self.unit,
            "price_delta": self.price_delta,
        }
