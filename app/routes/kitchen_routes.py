from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db, emit_customer_notification
from app.models.notification import Notification
from app.models.order import Order

kitchen = Blueprint("kitchen", __name__, url_prefix="/kitchen")


@kitchen.route("/dashboard")
@login_required
def dashboard():
    if current_user.role not in ["chef", "admin"]:
        flash("Access denied. Kitchen only.", "danger")
        return redirect(url_for("main.dashboard"))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    pending_orders = Order.query.filter_by(status="pending").all()
    preparing_orders = Order.query.filter_by(status="preparing").all()
    ready_orders = Order.query.filter_by(status="ready").all()

    return render_template(
        "kitchen/dashboard.html",
        user=current_user,
        orders=orders,
        pending_orders=pending_orders,
        preparing_orders=preparing_orders,
        ready_orders=ready_orders,
    )


@kitchen.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    if current_user.role not in ["chef", "admin"]:
        flash("Access denied.", "danger")
        return redirect(url_for("main.dashboard"))

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", "pending")
    allowed_statuses = ["pending", "preparing", "ready", "completed", "cancelled"]

    if new_status not in allowed_statuses:
        flash("Invalid order status.", "danger")
        return redirect(url_for("kitchen.dashboard"))

    order.status = new_status

    if new_status in ["ready", "completed"] and order.customer_id:
        message = "Your order is ready for pickup." if new_status == "ready" else "Your order has been completed."
        db.session.add(Notification(user_id=order.customer_id, message=message, read=False))

    db.session.commit()
    if new_status in ["ready", "completed"] and order.customer_id:
        emit_customer_notification(order.customer_id, order.id, message)
    flash(f"Order #{order.id} updated to {new_status}.", "success")
    return redirect(url_for("kitchen.dashboard"))
