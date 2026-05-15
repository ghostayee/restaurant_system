from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO

# Extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()

login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app)

    # ==================== REGISTER MODELS ====================
    with app.app_context():
        import app.models.user
        import app.models.customer  # Customer Model

    # ==================== REGISTER BLUEPRINTS ====================
    from app.routes.auth_routes import auth
    from app.routes.main_routes import main
    from app.routes.customer_routes import customer  # ← Added

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(customer)  # ← Added

    return app


# User Loader (for Staff)
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User

    return User.query.get(int(user_id))
