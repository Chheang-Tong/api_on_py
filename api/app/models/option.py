# --- app/models/option.py ---
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
        lazy="joined",
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
    option_id = db.Column(db.Integer, db.ForeignKey("option.id"), nullable=False)

    # ✅ Add a human-readable label for the value (e.g., "Large", "Red", "500g")
    label = db.Column(db.String(120), nullable=False)

    # Optional unit (e.g., "g", "cm"); keep if you need it
    unit = db.Column(db.String(50), nullable=True)

    price_delta = db.Column(db.Float, nullable=False, default=0.0)

    # ✅ compatibility for code that expects .value
    @property
    def value(self) -> str:
        return self.label

    def as_dict(self):
        return {
            "id": self.id,
            "option_id": self.option_id,
            "label": self.label,
            "unit": self.unit,
            "price_delta": float(self.price_delta or 0.0),
        }
