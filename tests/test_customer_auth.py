import unittest

from app import create_app, db
from app.models.customer import Customer


class CustomerAuthTests(unittest.TestCase):
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

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_customer_can_login_and_be_loaded(self):
        with self.app.app_context():
            customer = Customer(full_name="Test Customer", email="customer@example.com", phone="0712345678")
            customer.set_password("password123")
            db.session.add(customer)
            db.session.commit()

        response = self.client.post(
            "/customer/login",
            data={"email": "customer@example.com", "password": "password123"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            self.assertIn("_user_id", session)


if __name__ == "__main__":
    unittest.main()
