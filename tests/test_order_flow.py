import unittest

from app import create_app, db
from app.models.customer import Customer
from app.models.notification import Notification
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
            chef = User(username="chef1", email="chef@example.com", full_name="Chef One", role="chef")
            chef.set_password("secret")
            db.session.add(waiter)
            db.session.add(chef)
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

    def test_order_submission_notifies_waiter_chef_and_customer(self):
        with self.app.app_context():
            customer = Customer(full_name="Jane Doe", email="jane@example.com", phone="0712345679")
            customer.set_password("secret")
            db.session.add(customer)
            db.session.commit()

        with self.app.test_client() as client:
            login_response = client.post(
                "/customer/login",
                data={"email": "jane@example.com", "password": "secret"},
                follow_redirects=True,
            )
            self.assertEqual(login_response.status_code, 200)

            with client.session_transaction() as session:
                session["customer_cart"] = {
                    "1": {"id": 1, "name": "Classic Burger", "price": 12.5, "quantity": 1}
                }
                session["customer_table_id"] = 1

            response = client.post(
                "/customer/order",
                data={"notes": "extra ketchup"},
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            order = Order.query.first()
            self.assertIsNotNone(order)
            waiter = User.query.filter_by(role="waiter").first()
            chef = User.query.filter_by(role="chef").first()
            customer = Customer.query.filter_by(email="jane@example.com").first()

            notifications = Notification.query.filter(Notification.user_id.in_([customer.id, waiter.id, chef.id])).all()
            self.assertGreaterEqual(len(notifications), 3)
            self.assertTrue(any("New order" in note.message for note in notifications if note.user_id == waiter.id))
            self.assertTrue(any("New order" in note.message for note in notifications if note.user_id == chef.id))
            self.assertTrue(any("received" in note.message.lower() for note in notifications if note.user_id == customer.id))


if __name__ == "__main__":
    unittest.main()
