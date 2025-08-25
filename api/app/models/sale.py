# app/models/sale.py
from ..extensions import db

class Sale(db.Model):
    __tablename__ = "sale"  # optional but explicit
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)
    total = db.Column(db.Float, nullable=False, default=0.0)
