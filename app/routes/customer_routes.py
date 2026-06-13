from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.table import RestaurantTable
from app.models.user import User

customer = Blueprint("customer", __name__, url_prefix="/customer")


def _get_cart():
    return session.get("customer_cart", {})


def _save_cart(cart):
    session["customer_cart"] = cart


def _cart_count(cart):
    return sum(item["quantity"] for item in cart.values())


#CUSTOMER HOMEPAGE
@customer.route("/")
def index():
    return render_template("customer/index.html")


#CUSTOMER REGISTER
@customer.route("/register", methods=["GET", "POST"])
def register():
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
def menu():
    categories = Category.query.all()
    cart = _get_cart()
    return render_template('customer/menu.html', categories=categories, cart_count=_cart_count(cart))


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


@customer.route('/order', methods=['GET', 'POST'])
def order():
    cart = _get_cart()
    cart_items = list(cart.values())
    cart_total = sum(item['price'] * item['quantity'] for item in cart_items)

    if request.method == 'POST':
        if not cart_items:
            flash("Your cart is empty.", "warning")
            return redirect(url_for('customer.menu'))

        table = RestaurantTable.query.order_by(RestaurantTable.id).first()
        waiter = User.query.filter_by(role='waiter').first() or User.query.filter_by(role='admin').first() or User.query.first()

        if not table or not waiter:
            flash("Please create at least one table and one staff account before placing an order.", "warning")
            return redirect(url_for('customer.menu'))

        order_record = Order(
            table_id=table.id,
            waiter_id=waiter.id,
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
        session.pop('customer_cart', None)
        flash("Order placed successfully. The kitchen has been notified.", "success")
        return redirect(url_for('customer.menu'))

    return render_template(
        'customer/order.html',
        cart_items=cart_items,
        cart_total=round(cart_total, 2),
        cart_count=_cart_count(cart),
    )


#LOGOUT
@customer.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("customer.index"))
