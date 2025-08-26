from flask import Blueprint

bp = Blueprint("option", __name__,url_prefix="/api/options")

from . import routes 