from app import create_app, db
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.table import RestaurantTable
from app.models.user import User

app = create_app()
app.config.update(TESTING=True, SECRET_KEY='test-secret', SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False)
client = app.test_client()

with app.app_context():
    db.drop_all(); db.create_all()
    user = User(username='admin11', email='admin11@example.com', full_name='Admin Eleven', role='admin')
    user.set_password('secret'); db.session.add(user); db.session.flush()
    table = RestaurantTable(table_number='T15', capacity=4, status='available'); db.session.add(table); db.session.flush()
    customer = Customer(full_name='Jane Doe', email='jane2@example.com', phone='0711111116'); customer.set_password('secret'); db.session.add(customer); db.session.flush()
    category = Category(name='Dinner', description='Dinner items'); db.session.add(category); db.session.flush()
    product = Product(name='Pizza Slice', description='Cheesy', price=9.5, category_id=category.id, available=True); db.session.add(product); db.session.flush()
    order = Order(table_id=table.id, waiter_id=user.id, customer_id=customer.id, total_amount=19.0, status='completed', payment_status='paid'); db.session.add(order); db.session.flush()
    db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=2, notes='Extra cheese'))
    db.session.commit(); cid=customer.id; oid=order.id

with client.session_transaction() as session:
    session['_user_id'] = str(cid)
    session['_fresh'] = True

resp = client.post(f'/customer/orders/{oid}/reorder', follow_redirects=False)
print('STATUS', resp.status_code)
print('LOCATION', resp.headers.get('Location'))
with client.session_transaction() as session:
    cart = session.get('customer_cart', {})
    print('CART', cart)
