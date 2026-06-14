import unittest

from app import create_app, db
from app.models.customer import Customer
from app.models.notification import Notification
from app.models.order import Order
from app.models.table import RestaurantTable
from app.models.user import User


class CustomerNotificationsTests(unittest.TestCase):
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

            user = User(username="admin7", email="admin7@example.com", full_name="Admin Seven", role="admin")
            user.set_password("secret")
            db.session.add(user)
            db.session.flush()

            table = RestaurantTable(table_number="T11", capacity=4, status="occupied")
            db.session.add(table)
            db.session.flush()

            customer = Customer(full_name="Jane Doe", email="jane@example.com", phone="0711111111")
            customer.set_password("secret")
            db.session.add(customer)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=user.id, customer_id=customer.id, total_amount=15.0, status="pending")
            db.session.add(order)
            db.session.commit()

            self.order_id = order.id
            self.customer_id = customer.id
            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_ready_status_creates_notification_for_customer(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user_id)
            session["_fresh"] = True

        response = self.client.post(
            f"/orders/{self.order_id}/status",
            data={"status": "ready"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            notifications = Notification.query.filter_by(user_id=self.customer_id).all()
        self.assertTrue(notifications)
        self.assertIn("ready", notifications[0].message.lower())


if __name__ == "__main__":
    unittest.main()
