import unittest

from app import create_app, db
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.table import RestaurantTable
from app.models.user import User


class OrderDetailTests(unittest.TestCase):
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

            user = User(username="admin5", email="admin5@example.com", full_name="Admin Five", role="admin")
            user.set_password("secret")
            db.session.add(user)
            db.session.flush()

            table = RestaurantTable(table_number="T9", capacity=4, status="occupied")
            db.session.add(table)
            db.session.flush()

            category = Category(name="Bites", description="Small plates")
            db.session.add(category)
            db.session.flush()

            product = Product(name="Pizza Slice", description="Cheesy", price=4.5, category_id=category.id, available=True)
            db.session.add(product)
            db.session.flush()

            order = Order(table_id=table.id, waiter_id=user.id, total_amount=9.0, status="pending")
            db.session.add(order)
            db.session.flush()

            db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=2, notes="Extra cheese"))
            db.session.commit()

            self.user_id = user.id
            self.order_id = order.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_staff_can_view_order_details(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user_id)
            session["_fresh"] = True

        response = self.client.get(f"/orders/{self.order_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pizza Slice", response.data)
        self.assertIn(b"Extra cheese", response.data)


if __name__ == "__main__":
    unittest.main()
