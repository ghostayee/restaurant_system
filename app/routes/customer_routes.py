from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, ensure_database_ready
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.table import RestaurantTable
from app.models.user import User
from app.models.notification import Notification
from app.models.offer import Offer
from app import emit_customer_notification

customer = Blueprint("customer", __name__, url_prefix="/customer")


def _get_cart():
    return session.get("customer_cart", {})


def _save_cart(cart):
    session["customer_cart"] = cart


def _cart_count(cart):
    return sum(item["quantity"] for item in cart.values())


def _get_selected_table():
    table_id = session.get("customer_table_id")
    if table_id:
        return RestaurantTable.query.get(table_id)
    return RestaurantTable.query.order_by(RestaurantTable.id).first()


#CUSTOMER HOMEPAGE
@customer.route("/")
def index():
    return render_template("customer/index.html")


#CUSTOMER REGISTER
@customer.route("/register", methods=["GET", "POST"])
def register():
    ensure_database_ready()
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")

        if Customer.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for("customer.register"))

        new_customer = Customer(full_name=full_name, email=email, phone=phone)
        new_customer.set_password(password)

        db.session.add(new_customer)
        db.session.commit()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("customer.login"))

    return render_template("customer/register.html")


#CUSTOMER LOGIN
@customer.route("/login", methods=["GET", "POST"])
def login():
    ensure_database_ready()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        customer = Customer.query.filter_by(email=email).first()

        if customer and customer.check_password(password):
            login_user(customer)
            flash(f"Welcome, {customer.full_name}!", "success")
            return redirect(url_for("customer.index"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("customer/login.html")


#MENU PAGE
@customer.route('/menu')
@customer.route('/menu/<int:table_id>')
def menu(table_id=None):
    if table_id is not None:
        session["customer_table_id"] = table_id
    elif request.args.get("table_id"):
        session["customer_table_id"] = int(request.args.get("table_id"))

    categories = Category.query.all()
    offers = Offer.query.filter_by(active=True).order_by(Offer.created_at.desc()).all()
    cart = _get_cart()
    selected_table = _get_selected_table()
    return render_template(
        'customer/menu.html',
        categories=categories,
        offers=offers,
        cart_count=_cart_count(cart),
        selected_table=selected_table,
    )


@customer.route('/menu/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = _get_cart()
    item_key = str(product.id)

    if item_key in cart:
        cart[item_key]['quantity'] += 1
    else:
        cart[item_key] = {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'quantity': 1,
        }

    _save_cart(cart)
    flash(f"{product.name} added to your order.", "success")
    return redirect(request.referrer or url_for('customer.menu'))


@customer.route('/orders')
@login_required
def orders():
    customer_orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, read=False).order_by(Notification.created_at.desc()).all()
    return render_template('customer/orders.html', orders=customer_orders, notifications=notifications)


@customer.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.read = True
    db.session.commit()
    flash('Notification marked as read.', 'success')
    return redirect(url_for('customer.orders'))


@customer.route('/orders/<int:order_id>')
@login_required
def order_receipt(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    return render_template('customer/receipt.html', order=order)


@customer.route('/orders/<int:order_id>/reorder', methods=['POST'])
@login_required
def reorder_order(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    cart = _get_cart()

    for item in order.items:
        product = item.product
        if not product:
            continue
        item_key = str(product.id)
        if item_key in cart:
            cart[item_key]['quantity'] += item.quantity
        else:
            cart[item_key] = {
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'quantity': item.quantity,
            }

    _save_cart(cart)
    flash('Previous order added back to your cart.', 'success')
    return redirect(url_for('customer.menu'))


@customer.route('/order', methods=['GET', 'POST'])
def order():
    ensure_database_ready()
    cart = _get_cart()
    cart_items = list(cart.values())
    cart_total = sum(item['price'] * item['quantity'] for item in cart_items)
    selected_table = _get_selected_table()

    if request.method == 'POST':
        if not cart_items:
            flash("Your cart is empty.", "warning")
            return redirect(url_for('customer.menu'))

        waiter = User.query.filter_by(role='waiter').first() or User.query.filter_by(role='admin').first() or User.query.first()

        if not selected_table or not waiter:
            flash("Please create at least one table and one staff account before placing an order.", "warning")
            return redirect(url_for('customer.menu'))

        customer_record = None
        if not current_user.is_authenticated and request.form.get('create_account') == 'on':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '')

            if not full_name or not email or not password:
                flash("Please provide your name, email, and password to create an account.", "warning")
                return redirect(url_for('customer.order'))

            if Customer.query.filter_by(email=email).first():
                flash("An account with that email already exists. Please log in instead.", "warning")
                return redirect(url_for('customer.order'))

            customer_record = Customer(full_name=full_name, email=email, phone=phone)
            customer_record.set_password(password)
            db.session.add(customer_record)
            db.session.flush()
            login_user(customer_record)

        order_record = Order(
            table_id=selected_table.id,
            waiter_id=waiter.id,
            customer_id=current_user.id if current_user.is_authenticated else (customer_record.id if customer_record else None),
            total_amount=round(cart_total, 2),
            status='pending',
            payment_status='unpaid',
        )
        db.session.add(order_record)
        db.session.flush()

        for item in cart_items:
            db.session.add(
                OrderItem(
                    order_id=order_record.id,
                    product_id=item['id'],
                    quantity=item['quantity'],
                    notes=request.form.get('notes', ''),
                )
            )

        db.session.commit()

        if current_user.is_authenticated or customer_record:
            customer_user_id = current_user.id if current_user.is_authenticated else customer_record.id
            db.session.add(Notification(user_id=customer_user_id, message=f"Your order #{order_record.id} has been received and is now pending.", read=False))

        if waiter:
            db.session.add(Notification(user_id=waiter.id, message=f"New order #{order_record.id} needs attention from the waiter.", read=False))

        if waiter and waiter.role != 'chef':
            chef_user = User.query.filter_by(role='chef').first()
            if chef_user:
                db.session.add(Notification(user_id=chef_user.id, message=f"New order #{order_record.id} is waiting for preparation.", read=False))

        db.session.commit()

        if current_user.is_authenticated or customer_record:
            customer_user_id = current_user.id if current_user.is_authenticated else customer_record.id
            emit_customer_notification(customer_user_id, order_record.id, f"Your order #{order_record.id} has been received and is pending.")

        session.pop('customer_cart', None)
        if customer_record:
            flash("Order placed successfully. Your account is ready so you can track this order later.", "success")
        else:
            flash("Order placed successfully. The kitchen has been notified.", "success")
        return redirect(url_for('customer.menu'))

    return render_template(
        'customer/order.html',
        cart_items=cart_items,
        cart_total=round(cart_total, 2),
        cart_count=_cart_count(cart),
        selected_table=selected_table,
    )


#LOGOUT
@customer.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("customer.index"))
