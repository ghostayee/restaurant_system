from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.table import RestaurantTable

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


@main.route('/tables')
@login_required
def tables():
    tables = RestaurantTable.query.order_by(RestaurantTable.table_number).all()
    return render_template('tables.html', tables=tables)


@main.route('/tables/<int:table_id>/toggle-status')
@login_required
def toggle_table_status(table_id):
    table = RestaurantTable.query.get_or_404(table_id)
    statuses = ["available", "occupied", "reserved"]
    current_status = table.status or "available"
    next_index = (statuses.index(current_status) + 1) % len(statuses)
    table.status = statuses[next_index]
    db.session.commit()
    flash(f"Table {table.table_number} is now {table.status}.", "success")
    return redirect(url_for("main.tables"))