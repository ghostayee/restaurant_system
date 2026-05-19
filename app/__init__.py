from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
mail = Mail()

login_manager.login_view = "auth.login"


def create_app():
    """Create Flask App"""
    flask_app = Flask(__name__)
    flask_app.config.from_object("config.Config")

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    socketio.init_app(flask_app)
    mail.init_app(flask_app)

    # Register Models
    with flask_app.app_context():
        import app.models.user
        import app.models.customer
        import app.models.product

    # Register Blueprints
    from app.routes.auth_routes import auth
    from app.routes.main_routes import main
    from app.routes.customer_routes import customer
    from app.routes.waiter_routes import waiter

    flask_app.register_blueprint(auth)
    flask_app.register_blueprint(main)
    flask_app.register_blueprint(customer)
    flask_app.register_blueprint(waiter)

    return flask_app


@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User

    return User.query.get(int(user_id))
