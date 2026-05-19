from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.customer import Customer
from app.models.product import Category

customer = Blueprint("customer", __name__, url_prefix="/customer")


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
    return render_template('customer/menu.html', categories=categories)

#LOGOUT
@customer.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("customer.index"))
