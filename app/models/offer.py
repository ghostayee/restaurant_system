from app import db
from datetime import datetime


class Offer(db.Model):
    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    discount = db.Column(db.Float, nullable=False, default=0.0)
    image_url = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Offer {self.title} - {self.discount}%>"
