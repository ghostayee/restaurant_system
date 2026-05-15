from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO

# extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()

# Login Manager Configuration
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app)

        # Register Models
    with app.app_context():
        import app.models.user

    # Register Blueprints
    from app.routes.auth_routes import auth
    from app.routes.main_routes import main

    app.register_blueprint(auth)
    app.register_blueprint(main)

    return app


# User Loader (Must be outside create_app)
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User

    return User.query.get(int(user_id))
