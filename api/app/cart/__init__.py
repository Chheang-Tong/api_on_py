from flask import Blueprint

bp = Blueprint("cart", __name__, url_prefix="/api/cart")

print(">>> app.cart.__init__: blueprint created") 

from . import routes 