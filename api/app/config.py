import os

class Config:
    # DB in instance folder
    # NOTE: when running, Flask sets app.instance_path; we refer to it in __init__.py by joining
    SQLALCHEMY_DATABASE_URI = "sqlite:///"  # placeholder; final path built by __init__ via db.create_all()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
