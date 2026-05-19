from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

waiter = Blueprint("waiter", __name__, url_prefix="/waiter")


@waiter.route("/dashboard")
@login_required
def dashboard():
    if current_user.role not in ["waiter", "admin"]:
        flash("Access denied. Waiter only.", "danger")
        return redirect(url_for("main.dashboard"))

    return render_template("waiter/dashboard.html", user=current_user)
