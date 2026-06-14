import unittest

from app import create_app, db
from app.models.product import Category, Product
from app.models.user import User


class MenuManagementTests(unittest.TestCase):
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

            user = User(username="admin3", email="admin3@example.com", full_name="Admin Three", role="admin")
            user.set_password("secret")
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_staff_can_create_category_and_toggle_product_availability(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user_id)
            session["_fresh"] = True

        response = self.client.post(
            "/menu-management",
            data={"action": "create_category", "name": "Drinks", "description": "Fresh beverages"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Drinks", response.data)

        with self.app.app_context():
            category = Category.query.filter_by(name="Drinks").first()
        self.assertIsNotNone(category)

        response = self.client.post(
            "/menu-management",
            data={
                "action": "create_product",
                "name": "Mango Smoothie",
                "description": "Cold mango delight",
                "price": "5.50",
                "category_id": str(category.id),
                "image_url": "https://example.com/mango.jpg",
                "available": "on",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mango Smoothie", response.data)

        with self.app.app_context():
            product = Product.query.filter_by(name="Mango Smoothie").first()
        self.assertIsNotNone(product)
        self.assertTrue(product.available)
        self.assertEqual(product.image_url, "https://example.com/mango.jpg")

        response = self.client.post(
            "/menu-management",
            data={"action": "toggle_product", "product_id": str(product.id)},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            product = Product.query.get(product.id)
        self.assertFalse(product.available)

    def test_staff_can_edit_and_delete_products(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user_id)
            session["_fresh"] = True

        with self.app.app_context():
            category = Category(name="Snacks", description="Quick bites")
            db.session.add(category)
            db.session.commit()
            db.session.refresh(category)
            category_id = category.id
            product = Product(name="Fries", description="Crispy fries", price=3.5, category_id=category_id, available=True)
            db.session.add(product)
            db.session.commit()
            db.session.refresh(product)
            product_id = product.id

        response = self.client.post(
            "/menu-management",
            data={
                "action": "edit_product",
                "product_id": str(product_id),
                "name": "Loaded Fries",
                "description": "With cheese",
                "price": "4.50",
                "category_id": str(category_id),
                "available": "on",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Loaded Fries", response.data)

        with self.app.app_context():
            edited_product = Product.query.get(product_id)
        self.assertEqual(edited_product.name, "Loaded Fries")
        self.assertEqual(float(edited_product.price), 4.5)

        response = self.client.post(
            "/menu-management",
            data={"action": "delete_product", "product_id": str(product_id)},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            deleted_product = Product.query.get(product_id)
        self.assertIsNone(deleted_product)


if __name__ == "__main__":
    unittest.main()
