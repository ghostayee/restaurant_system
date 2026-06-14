import unittest

from app import create_app, db
from app.models.customer import Customer
from app.models.notification import Notification


class NotificationReadTests(unittest.TestCase):
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

            customer = Customer(full_name="Jane Doe", email="jane2@example.com", phone="0711111112")
            customer.set_password("secret")
            db.session.add(customer)
            db.session.commit()

            notification = Notification(user_id=customer.id, message="Your order is ready", read=False)
            db.session.add(notification)
            db.session.commit()

            self.customer_id = customer.id
            self.notification_id = notification.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_customer_can_mark_notification_as_read(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.customer_id)
            session["_fresh"] = True

        response = self.client.post(f"/customer/notifications/{self.notification_id}/read", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            updated = Notification.query.get(self.notification_id)
        self.assertTrue(updated.read)


if __name__ == "__main__":
    unittest.main()
