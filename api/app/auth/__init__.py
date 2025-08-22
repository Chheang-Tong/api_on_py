from flask import Blueprint
bp = Blueprint("auth", __name__)

from . import routes  # keep this import so routes register
