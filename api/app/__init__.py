# app/__init__.py
import os
from flask import Flask, jsonify
from .extensions import db, jwt, cors
from .extensions import db, migrate



def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Ensure instance folder exists and set SQLite DB there
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, "app.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI",f"sqlite:///{db_path}",)
    db_path = os.path.join(app.instance_path, "app.db") 
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"


    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})
    migrate.init_app(app, db)


    # Register blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    # products blueprint
    from .products import bp as products_bp
    app.register_blueprint(products_bp)
    # categories blueprint
    from .category import bp as categories_bp
    app.register_blueprint(categories_bp)
    #options blueprint
    from .option import bp as options_bp
    app.register_blueprint(options_bp)


    @app.get("/")
    def health():
        return jsonify(ok=True, msg="API running")

    # Dev: create tables
    with app.app_context():
        db.create_all()

    return app
