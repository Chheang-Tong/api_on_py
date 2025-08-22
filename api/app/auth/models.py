from ..extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(180), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(100), nullable=False,default="")

    def as_dict(self):
        return {"id": self.id, "email": self.email, "name": self.name}
