import unittest

from app import create_app, db
from app.models.customer import Customer
from app.models.order import Order
from app.models.table import RestaurantTable
from app.models.user import User


class CompletedOrderSummaryTests(unittest.TestCase):
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

            user = User(username="admin8", email="admin8@example.com", full_name="Admin Eight", role="admin")
            user.set_password("secret")
            db.session.add(user)
            db.session.flush()

            table = RestaurantTable(table_number="T12", capacity=4, status="occupied")
            db.session.add(table)
            db.session.flush()

            customer = Customer(full_name="Janet Doe", email="janet@example.com", phone="0711111113")
            customer.set_password("secret")
            db.session.add(customer)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=user.id, customer_id=customer.id, total_amount=25.0, status="completed", payment_status="paid")
            db.session.add(order)
            db.session.commit()

            self.customer_id = customer.id
            self.order_id = order.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_completed_orders_show_payment_summary(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.customer_id)
            session["_fresh"] = True

        response = self.client.get('/customer/orders')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'paid', response.data.lower())
        self.assertIn(b'completed', response.data.lower())


if __name__ == "__main__":
    unittest.main()
