import unittest

from app import create_app, db
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.table import RestaurantTable
from app.models.user import User


class ReceiptViewTests(unittest.TestCase):
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

            user = User(username="admin9", email="admin9@example.com", full_name="Admin Nine", role="admin")
            user.set_password("secret")
            db.session.add(user)
            db.session.flush()

            table = RestaurantTable(table_number="T13", capacity=4, status="occupied")
            db.session.add(table)
            db.session.flush()

            customer = Customer(full_name="John Doe", email="john@example.com", phone="0711111114")
            customer.set_password("secret")
            db.session.add(customer)
            db.session.flush()

            category = Category(name="Lunch", description="Lunch items")
            db.session.add(category)
            db.session.flush()

            product = Product(name="Rice Plate", description="Delicious", price=8.0, category_id=category.id, available=True)
            db.session.add(product)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=user.id, customer_id=customer.id, total_amount=16.0, status="completed", payment_status="paid")
            db.session.add(order)
            db.session.flush()

            db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=2, notes="No onions"))
            db.session.commit()

            self.customer_id = customer.id
            self.order_id = order.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_customer_can_view_receipt_style_order_page(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.customer_id)
            session["_fresh"] = True

        response = self.client.get(f"/customer/orders/{self.order_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Receipt", response.data)
        self.assertIn(b"Rice Plate", response.data)


if __name__ == "__main__":
    unittest.main()
