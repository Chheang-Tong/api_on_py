from flask import Blueprint
bp = Blueprint("sales", __name__)

from . import routes  # noqa
