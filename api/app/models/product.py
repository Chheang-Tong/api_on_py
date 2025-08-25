from ..extensions import db

# ---------------- CATEGORY ----------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    products = db.relationship("Product", backref="category", lazy=True)

    def as_dict(self):
        return {"id": self.id, "name": self.name}


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
