from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.order import Order
from app.models.table import RestaurantTable

waiter = Blueprint("waiter", __name__, url_prefix="/waiter")


@waiter.route("/dashboard")
@login_required
def dashboard():
    if current_user.role not in ["waiter", "admin"]:
        flash("Access denied. Waiter only.", "danger")
        return redirect(url_for("main.dashboard"))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("waiter/dashboard.html", user=current_user, orders=orders)


@waiter.route('/tables')
@login_required
def tables():
    tables = RestaurantTable.query.all()
    return render_template('tables.html', tables=tables)


@waiter.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    if current_user.role not in ["waiter", "admin"]:
        flash("Access denied.", "danger")
        return redirect(url_for("main.dashboard"))

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status', 'pending')
    allowed_statuses = ["pending", "preparing", "ready", "completed", "cancelled"]

    if new_status not in allowed_statuses:
        flash("Invalid order status.", "danger")
        return redirect(url_for("waiter.dashboard"))

    order.status = new_status
    db.session.commit()
    flash(f"Order #{order.id} status updated to {new_status}.", "success")
    return redirect(url_for("waiter.dashboard"))