import unittest

from app import create_app, db
from app.models.user import User


class OffersTests(unittest.TestCase):
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

            admin = User(username="admin_offer", email="admin_offer@example.com", full_name="Offer Admin", role="admin")
            admin.set_password("secret")
            db.session.add(admin)
            db.session.commit()
            self.admin_id = admin.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_offer_model_can_be_created(self):
        with self.app.app_context():
            from app.models.offer import Offer

            offer = Offer(title="Lunch Special", description="10% off", discount=10.0)
            db.session.add(offer)
            db.session.commit()

            saved = Offer.query.first()
            self.assertEqual(saved.title, "Lunch Special")
            self.assertEqual(saved.discount, 10.0)

    def test_admin_can_create_offer_via_management_route(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin_id)
            session["_fresh"] = True

        response = self.client.post(
            "/offers-management",
            data={
                "action": "create_offer",
                "title": "Weekend Deal",
                "description": "Free drink with burger",
                "discount": "15",
                "image_url": "https://example.com/offer.jpg",
                "active": "on",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            from app.models.offer import Offer

            offer = Offer.query.filter_by(title="Weekend Deal").first()
            self.assertIsNotNone(offer)
            self.assertEqual(offer.discount, 15.0)
            self.assertEqual(offer.image_url, "https://example.com/offer.jpg")


if __name__ == "__main__":
    unittest.main()
