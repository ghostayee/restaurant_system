from app import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('restaurant_tables.id'), nullable=False)
    waiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')   # pending, preparing, ready, completed, cancelled
    payment_status = db.Column(db.String(20), default='unpaid')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Order #{self.id} - Table {self.table_id}>"


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String(200))

    product = db.relationship('Product', backref='order_items', lazy=True)

    def __repr__(self):
        return f"<OrderItem {self.quantity}x Product {self.product_id}>"