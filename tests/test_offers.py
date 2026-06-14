import unittest

from app import create_app, db


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


if __name__ == "__main__":
    unittest.main()
