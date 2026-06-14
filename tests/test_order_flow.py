import unittest

from app import create_app, db
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.table import RestaurantTable
from app.models.user import User


class OrderFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            category = Category(name="Burgers")
            db.session.add(category)
            db.session.flush()

            product = Product(name="Classic Burger", description="test", price=12.5, category_id=category.id, available=True)
            db.session.add(product)

            table = RestaurantTable(table_number="T1", capacity=4, status="available")
            db.session.add(table)

            waiter = User(username="waiter1", email="waiter@example.com", full_name="Waiter One", role="waiter")
            waiter.set_password("secret")
            db.session.add(waiter)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_customer_can_create_order_with_items(self):
        with self.app.app_context():
            product = Product.query.filter_by(name="Classic Burger").first()
            table = RestaurantTable.query.first()
            waiter = User.query.filter_by(role="waiter").first()

            order = Order(table_id=table.id, waiter_id=waiter.id, total_amount=12.5, status="pending")
            db.session.add(order)
            db.session.flush()

            db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=1, notes="no onions"))
            db.session.commit()

        with self.app.app_context():
            saved_order = Order.query.first()
            self.assertIsNotNone(saved_order)
            self.assertEqual(saved_order.total_amount, 12.5)
            self.assertEqual(OrderItem.query.count(), 1)


if __name__ == "__main__":
    unittest.main()
