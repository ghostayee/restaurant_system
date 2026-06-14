import unittest

from app import create_app, db
from app.models.order import Order
from app.models.table import RestaurantTable
from app.models.user import User


class OrderSearchTests(unittest.TestCase):
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

            user = User(username="admin4", email="admin4@example.com", full_name="Admin Four", role="admin")
            user.set_password("secret")
            db.session.add(user)
            db.session.flush()

            table = RestaurantTable(table_number="T8", capacity=4, status="occupied")
            db.session.add(table)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=user.id, total_amount=18.5, status="pending")
            db.session.add(order)
            db.session.commit()

            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_staff_can_search_orders_by_status_and_table(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user_id)
            session["_fresh"] = True

        response = self.client.get("/order-search?status=pending&table=T8")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Order #", response.data)
        self.assertIn(b"pending", response.data.lower())


if __name__ == "__main__":
    unittest.main()
