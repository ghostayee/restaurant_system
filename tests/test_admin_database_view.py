import unittest

from app import create_app, db
from app.models.customer import Customer
from app.models.offer import Offer
from app.models.product import Category, Product
from app.models.user import User


class AdminDatabaseViewTests(unittest.TestCase):
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

            admin = User(username="admin_db", email="admin_db@example.com", full_name="Database Admin", role="admin")
            admin.set_password("secret")
            db.session.add(admin)

            customer = Customer(full_name="Jane Doe", email="jane@example.com", phone="0712345678")
            customer.set_password("secret")
            db.session.add(customer)

            category = Category(name="Specials", description="Featured dishes")
            db.session.add(category)
            db.session.flush()

            product = Product(name="Spicy Pasta", description="Creamy pasta", price=10.5, category_id=category.id, image_url="https://example.com/pasta.jpg", available=True)
            db.session.add(product)

            offer = Offer(title="Weekend Special", description="Free drink", discount=15.0, image_url="https://example.com/offer.jpg", active=True)
            db.session.add(offer)
            db.session.commit()

            self.admin_id = admin.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_can_view_database_snapshot_page(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin_id)
            session["_fresh"] = True

        response = self.client.get("/database-view", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Database Snapshot", response.data)
        self.assertIn(b"Users", response.data)
        self.assertIn(b"Products", response.data)
        self.assertIn(b"Offers", response.data)

    def test_customer_menu_shows_active_offers_and_product_image(self):
        response = self.client.get("/customer/menu")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Weekend Special", response.data)
        self.assertIn(b"https://example.com/pasta.jpg", response.data)
