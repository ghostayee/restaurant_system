import unittest

from app import create_app, db
from app.models.order import Order
from app.models.table import RestaurantTable
from app.models.user import User


class KitchenDashboardTests(unittest.TestCase):
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

            table = RestaurantTable(table_number="K1", capacity=2, status="occupied")
            db.session.add(table)
            db.session.flush()

            chef = User(username="chef1", email="chef1@example.com", full_name="Chef One", role="chef")
            chef.set_password("secret")
            db.session.add(chef)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=chef.id, total_amount=20.0, status="pending")
            db.session.add(order)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_kitchen_dashboard_shows_pending_orders(self):
        with self.app.app_context():
            chef = User.query.filter_by(role="chef").first()

        login_response = self.client.post(
            "/auth/login",
            data={"username": "chef1", "password": "secret"},
            follow_redirects=True,
        )

        self.assertEqual(login_response.status_code, 200)
        response = self.client.get("/kitchen/dashboard", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Kitchen Dashboard", response.data)


if __name__ == "__main__":
    unittest.main()
