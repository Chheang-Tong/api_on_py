from flask import Blueprint
bp = Blueprint("sales", __name__, url_prefix="/api/sales")

from . import routes  # noqa
