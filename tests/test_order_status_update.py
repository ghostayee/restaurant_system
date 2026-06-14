import unittest

from app import create_app, db
from app.models.order import Order
from app.models.table import RestaurantTable
from app.models.user import User


class OrderStatusUpdateTests(unittest.TestCase):
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

            user = User(username="admin6", email="admin6@example.com", full_name="Admin Six", role="admin")
            user.set_password("secret")
            db.session.add(user)
            db.session.flush()

            table = RestaurantTable(table_number="T10", capacity=4, status="occupied")
            db.session.add(table)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=user.id, total_amount=20.0, status="pending")
            db.session.add(order)
            db.session.commit()
            self.order_id = order.id
            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_staff_can_update_order_status_from_detail_page(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user_id)
            session["_fresh"] = True

        response = self.client.post(
            f"/orders/{self.order_id}/status",
            data={"status": "preparing"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            updated_order = Order.query.get(self.order_id)
        self.assertEqual(updated_order.status, "preparing")


if __name__ == "__main__":
    unittest.main()
