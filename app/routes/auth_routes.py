from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User

auth = Blueprint("auth", __name__, url_prefix="/auth")


# ====================== STAFF LOGIN ======================
@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash(f"Welcome back, {user.full_name}!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("auth/login.html")


# ====================== STAFF REGISTER (Admin Only) ======================
@auth.route("/register", methods=["GET", "POST"])
def register():
    if not current_user.is_authenticated:
        flash("Please login first", "warning")
        return redirect(url_for("auth.login", next=request.url))

    if current_user.role != "admin":
        flash("Only Administrators can register new staff members.", "danger")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        full_name = request.form.get("full_name")
        password = request.form.get("password")
        role = request.form.get("role", "waiter")

        if User.query.filter_by(username=username).first():
            flash("Username already taken", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for("auth.register"))

        new_user = User(username=username, email=email, full_name=full_name, role=role)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash(f"Staff account for {full_name} created successfully!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")


# ====================== LOGOUT ======================
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))


# ====================== TEMPORARY: CREATE FIRST ADMIN ======================
@auth.route("/create-first-admin")
def create_first_admin():
    if User.query.filter_by(role="admin").first():
        flash("Admin account already exists!", "info")
        return redirect(url_for("auth.login"))

    admin = User(
        username="admin",
        email="admin@restro.com",
        full_name="System Administrator",
        role="admin",
    )
    admin.set_password("admin123")

    db.session.add(admin)
    db.session.commit()

    flash(
        "✅ First Admin created!<br>Username: <b>admin</b><br>Password: <b>admin123</b>",
        "success",
    )
    return redirect(url_for("auth.login"))
