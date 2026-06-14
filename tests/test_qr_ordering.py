import unittest

from app import create_app, db, socketio
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Category, Product
from app.models.table import RestaurantTable
from app.models.user import User


class QROrderingTests(unittest.TestCase):
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

            category = Category(name="Drinks")
            db.session.add(category)
            db.session.flush()

            product = Product(name="Tea", description="test", price=3.0, category_id=category.id, available=True)
            db.session.add(product)

            table = RestaurantTable(table_number="Q1", capacity=2, status="available")
            db.session.add(table)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_customer_can_view_table_order_page(self):
        response = self.client.get("/customer/menu")
        self.assertEqual(response.status_code, 200)

    def test_guest_can_place_order_and_create_account_for_tracking(self):
        with self.client.session_transaction() as session:
            session["customer_cart"] = {
                "1": {
                    "id": 1,
                    "name": "Tea",
                    "price": 3.0,
                    "quantity": 1,
                }
            }

        response = self.client.post(
            "/customer/order",
            data={
                "full_name": "Guest User",
                "email": "guest@example.com",
                "phone": "0711111111",
                "password": "guestpass",
                "create_account": "on",
                "notes": "extra ice",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            customer = Customer.query.filter_by(email="guest@example.com").first()
            order = Order.query.first()
            self.assertIsNotNone(customer)
            self.assertIsNotNone(order)
            self.assertEqual(order.customer_id, customer.id)

    def test_customer_room_receives_order_status_update_event(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()

            waiter = User(username="socket_waiter", email="socket_waiter@example.com", full_name="Socket Waiter", role="waiter")
            waiter.set_password("secret")
            db.session.add(waiter)

            table = RestaurantTable(table_number="S1", capacity=2, status="available")
            db.session.add(table)
            db.session.flush()

            customer = Customer(full_name="Socket Customer", email="socket_customer@example.com", phone="0712345678")
            customer.set_password("secret")
            db.session.add(customer)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=waiter.id, customer_id=customer.id, total_amount=12.0, status="pending", payment_status="unpaid")
            db.session.add(order)
            db.session.commit()
            customer_id = customer.id
            order_id = order.id

        customer_id = customer_id

        socket_client = socketio.test_client(self.app, flask_test_client=self.client)
        socket_client.emit("join_customer_room", {"customer_id": customer_id})

        with self.app.app_context():
            from app import emit_customer_notification
            emit_customer_notification(customer_id, order.id, "Your order is ready for pickup.")

        received = socket_client.get_received()
        self.assertTrue(any(event["name"] == "order_status_update" for event in received))


if __name__ == "__main__":
    unittest.main()
