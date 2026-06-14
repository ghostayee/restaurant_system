from app import db
from datetime import datetime


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    unit = db.Column(db.String(50), nullable=False, default="unit")
    minimum_level = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<InventoryItem {self.item_name} - {self.quantity} {self.unit}>"
