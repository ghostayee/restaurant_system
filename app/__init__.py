from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
mail = Mail()

login_manager.login_view = "auth.login"


@socketio.on("join_customer_room")
def handle_join_customer_room(data=None):
    customer_id = None
    if isinstance(data, dict):
        customer_id = data.get("customer_id")
    if customer_id:
        join_room(f"customer_{customer_id}")
        emit("joined_customer_room", {"customer_id": customer_id})


@socketio.on("leave_customer_room")
def handle_leave_customer_room(data=None):
    customer_id = None
    if isinstance(data, dict):
        customer_id = data.get("customer_id")
    if customer_id:
        leave_room(f"customer_{customer_id}")


def emit_customer_notification(customer_id, order_id, message):
    if not customer_id:
        return
    socketio.emit(
        "order_status_update",
        {
            "customer_id": customer_id,
            "order_id": order_id,
            "message": message,
        },
        room=f"customer_{customer_id}",
    )


def _seed_demo_data(flask_app):
    from app.models.customer import Customer
    from app.models.product import Category, Product
    from app.models.table import RestaurantTable
    from app.models.user import User

    with flask_app.app_context():
        for username, email, full_name, role in [
            ("admin", "admin@restro.com", "System Administrator", "admin"),
            ("waiter", "waiter@restro.com", "Test Waiter", "waiter"),
            ("chef", "chef@restro.com", "Test Chef", "chef"),
        ]:
            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                continue
            user = User(username=username, email=email, full_name=full_name, role=role)
            user.set_password("admin123" if role == "admin" else "waiter123" if role == "waiter" else "chef123")
            db.session.add(user)

        existing_customer = Customer.query.filter((Customer.email == "customer@restro.com") | (Customer.phone == "0712345678")).first()
        if not existing_customer:
            customer = Customer(full_name="Test Customer", email="customer@restro.com", phone="0712345678")
            customer.set_password("customer123")
            db.session.add(customer)

        featured_category = Category.query.filter_by(name="Featured").first()
        if not featured_category:
            featured_category = Category(name="Featured", description="Signature dishes")
            db.session.add(featured_category)
            db.session.flush()

        if not Product.query.filter_by(name="Burger Combo").first():
            db.session.add(Product(name="Burger Combo", description="Classic burger with fries", price=12.5, category_id=featured_category.id, available=True))

        if not Product.query.filter_by(name="Chicken Wrap").first():
            db.session.add(Product(name="Chicken Wrap", description="Grilled chicken wrap", price=9.5, category_id=featured_category.id, available=True))

        if not Product.query.filter_by(name="Veggie Pizza").first():
            db.session.add(Product(name="Veggie Pizza", description="Fresh mixed vegetable pizza", price=14.0, category_id=featured_category.id, available=True))

        burgers_category = Category.query.filter_by(name="Burgers").first()
        if not burgers_category:
            burgers_category = Category(name="Burgers", description="Fresh grilled burgers")
            db.session.add(burgers_category)
            db.session.flush()

        if not Product.query.filter_by(name="Beef Burger").first():
            db.session.add(Product(name="Beef Burger", description="Juicy beef burger", price=13.5, category_id=burgers_category.id, available=True))

        if not Product.query.filter_by(name="Chicken Burger").first():
            db.session.add(Product(name="Chicken Burger", description="Crispy chicken burger", price=11.5, category_id=burgers_category.id, available=True))

        drinks_category = Category.query.filter_by(name="Drinks").first()
        if not drinks_category:
            drinks_category = Category(name="Drinks", description="Cool drinks and refreshments")
            db.session.add(drinks_category)
            db.session.flush()

        if not Product.query.filter_by(name="Mango Juice").first():
            db.session.add(Product(name="Mango Juice", description="Fresh mango juice", price=4.5, category_id=drinks_category.id, available=True))

        if not Product.query.filter_by(name="Coke").first():
            db.session.add(Product(name="Coke", description="Cold soft drink", price=2.5, category_id=drinks_category.id, available=True))

        if not RestaurantTable.query.first():
            table = RestaurantTable(table_number="T1", capacity=4, status="available")
            db.session.add(table)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()


def ensure_database_ready(flask_app=None):
    if flask_app is None:
        from flask import current_app
        flask_app = current_app

    with flask_app.app_context():
        try:
            db.create_all()
        except Exception as exc:
            db.session.rollback()
            print(f"Database initialization warning: {exc}")
        _seed_demo_data(flask_app)

    return flask_app


def create_app():
    """Create Flask App"""
    flask_app = Flask(__name__)
    flask_app.config.from_object("config.Config")

    # extensions
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
        import app.models.table
        import app.models.order
        import app.models.inventory
        import app.models.offer
        import app.models.notification

        ensure_database_ready(flask_app)

    # Register Blueprints
    from app.routes.auth_routes import auth
    from app.routes.main_routes import main
    from app.routes.customer_routes import customer
    from app.routes.waiter_routes import waiter
    from app.routes.kitchen_routes import kitchen

    flask_app.register_blueprint(auth)
    flask_app.register_blueprint(main)
    flask_app.register_blueprint(customer)
    flask_app.register_blueprint(waiter)
    flask_app.register_blueprint(kitchen)

    return flask_app


@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    from app.models.customer import Customer

    user = User.query.get(int(user_id))
    if user:
        return user

    return Customer.query.get(int(user_id))
