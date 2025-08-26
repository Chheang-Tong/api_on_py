#  --- cart/routes.py ---
from flask import Blueprint,jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_, asc, desc
from ..models import Cart, CartItem, Product
from ..extensions import db
from . import bp