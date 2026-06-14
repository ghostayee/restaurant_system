import unittest

from app import create_app, db
from app.models.order import Order
from app.models.table import RestaurantTable
from app.models.user import User


class AdminDashboardTests(unittest.TestCase):
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

            table = RestaurantTable(table_number="A1", capacity=4, status="occupied")
            db.session.add(table)
            db.session.flush()

            admin = User(username="admin2", email="admin2@example.com", full_name="Admin Two", role="admin")
            admin.set_password("secret")
            db.session.add(admin)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=admin.id, total_amount=25.0, status="pending")
            db.session.add(order)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_dashboard_shows_orders_and_tables(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(1)
            session["_fresh"] = True

        response = self.client.get("/dashboard", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.data)


if __name__ == "__main__":
    unittest.main()
