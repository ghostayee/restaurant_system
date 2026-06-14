import unittest

from app import create_app, db


class InventoryTests(unittest.TestCase):
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

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_inventory_model_can_store_stock_and_threshold(self):
        with self.app.app_context():
            from app.models.inventory import InventoryItem

            item = InventoryItem(item_name="Tomatoes", quantity=12, unit="kg", minimum_level=5)
            db.session.add(item)
            db.session.commit()

            saved = InventoryItem.query.first()
            self.assertEqual(saved.quantity, 12)
            self.assertEqual(saved.minimum_level, 5)


if __name__ == "__main__":
    unittest.main()
