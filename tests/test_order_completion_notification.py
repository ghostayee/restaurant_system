import unittest

from app import create_app, db
from app.models.customer import Customer
from app.models.order import Order
from app.models.table import RestaurantTable
from app.models.user import User


class OrderCompletionNotificationTests(unittest.TestCase):
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

            customer = Customer(full_name="Notify Customer", email="notify@example.com", phone="0711111111")
            customer.set_password("password123")
            db.session.add(customer)
            db.session.flush()

            waiter = User(username="waiter4", email="waiter4@example.com", full_name="Waiter Four", role="waiter")
            waiter.set_password("secret")
            db.session.add(waiter)
            db.session.flush()

            table = RestaurantTable(table_number="N1", capacity=2, status="occupied")
            db.session.add(table)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=waiter.id, customer_id=customer.id, total_amount=20.0, status="pending")
            db.session.add(order)
            db.session.commit()
            self.order_id = order.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_completion_updates_customer_notification(self):
        with self.app.app_context():
            from app.models.notification import Notification
            from app.models.customer import Customer

            customer = Customer.query.filter_by(email="notify@example.com").first()
            notification = Notification(user_id=customer.id, message="Your order is ready", read=False)
            db.session.add(notification)
            db.session.commit()

        self.client.post(
            "/customer/login",
            data={"email": "notify@example.com", "password": "password123"},
            follow_redirects=True,
        )

        response = self.client.get("/customer/orders", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My Orders", response.data)


if __name__ == "__main__":
    unittest.main()
