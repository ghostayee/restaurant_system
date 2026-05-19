from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register Models
    with app.app_context():
        import app.models.user
        import app.models.customer

    # Register Blueprints
    from app.routes.auth_routes import auth
    from app.routes.main_routes import main
    from app.routes.customer_routes import customer

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(customer)

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User

    return User.query.get(int(user_id))
