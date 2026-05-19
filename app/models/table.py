from app import db
from datetime import datetime


class RestaurantTable(db.Model):
    __tablename__ = "restaurant_tables"

    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.String(20), unique=True, nullable=False)
    capacity = db.Column(db.Integer, default=4)
    status = db.Column(
        db.String(20), default="available"
    )  # available, occupied, reserved
    qr_code = db.Column(db.String(255))  # Will store QR code path or data
    current_order_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Table {self.table_number} - {self.status}>"
