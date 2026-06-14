import unittest

from app import create_app, db
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.table import RestaurantTable
from app.models.user import User


class ReorderOrderTests(unittest.TestCase):
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

            user = User(username="admin10", email="admin10@example.com", full_name="Admin Ten", role="admin")
            user.set_password("secret")
            db.session.add(user)
            db.session.flush()

            table = RestaurantTable(table_number="T14", capacity=4, status="available")
            db.session.add(table)
            db.session.flush()

            customer = Customer(full_name="Jane Doe", email="jane@example.com", phone="0711111115")
            customer.set_password("secret")
            db.session.add(customer)
            db.session.flush()

            category = Category(name="Dinner", description="Dinner items")
            db.session.add(category)
            db.session.flush()

            product = Product(name="Pizza Slice", description="Cheesy", price=9.5, category_id=category.id, available=True)
            db.session.add(product)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=user.id, customer_id=customer.id, total_amount=19.0, status="completed", payment_status="paid")
            db.session.add(order)
            db.session.flush()

            db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=2, notes="Extra cheese"))
            db.session.commit()

            self.customer_id = customer.id
            self.order_id = order.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_customer_can_reorder_previous_order(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.customer_id)
            session["_fresh"] = True

        response = self.client.post(f"/customer/orders/{self.order_id}/reorder", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            cart = session.get("customer_cart", {})
            self.assertIn("1", cart)
            self.assertEqual(cart["1"]["quantity"], 2)
            self.assertEqual(cart["1"]["name"], "Pizza Slice")


if __name__ == "__main__":
    unittest.main()
