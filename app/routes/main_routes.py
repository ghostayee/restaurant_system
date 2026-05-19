from flask import Blueprint, render_template
from flask_login import login_required, current_user
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
    tables = RestaurantTable.query.all()
    return render_template('tables.html', tables=tables)