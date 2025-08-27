from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
migrate = Migrate()

# def require_headers(f):
#     from functools import wraps
#     from flask import request, jsonify

#     @wraps(f)
#     def wrapper(*args, **kwargs):
#         required_headers = [
#             "Content-Type",
#             "Accept",
#             "Platform",
#             "Accept-Language",
#             "Ocp-Apim-Subscription-Key",
#         ]
#         missing = [h for h in required_headers if not request.headers.get(h)]
#         if missing:
#             return jsonify(msg=f"Missing required headers: {', '.join(missing)}"), 400
#         return f(*args, **kwargs)
#     return wrapper