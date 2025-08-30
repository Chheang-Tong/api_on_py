# --- app/models/user.py ---
from ..extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(180), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(100), nullable=False,default="")

    # New fields
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))  # supports IPv6
    last_login_lat = db.Column(db.Float)      # nullable
    last_login_lng = db.Column(db.Float)      # nullable
    device = db.Column(db.String(100),nullable=True)  # nullable

    def as_dict(self):
        return {
            "id": self.id, 
            "email": self.email, 
            "name": self.name,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "last_login_ip": self.last_login_ip,
            "last_login_lat": self.last_login_lat,
            "last_login_lng": self.last_login_lng,
            "device": self.device
            }
    
class RefreshToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
