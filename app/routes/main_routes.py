from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.inventory import InventoryItem
from app.models.order import Order
from app.models.table import RestaurantTable
from app.models.product import Category, Product
from app.models.notification import Notification
from app.models.offer import Offer
from app.models.customer import Customer
from app.models.user import User

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/dashboard")
@login_required
def dashboard():
    tables = RestaurantTable.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    pending_orders = Order.query.filter_by(status="pending").count()
    occupied_tables = RestaurantTable.query.filter_by(status="occupied").count()
    total_sales = sum(order.total_amount for order in orders)
    low_stock_items = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.minimum_level).count()

    return render_template(
        "dashboard.html",
        user=current_user,
        tables=tables,
        orders=orders,
        pending_orders=pending_orders,
        occupied_tables=occupied_tables,
        total_sales=total_sales,
        low_stock_items=low_stock_items,
    )


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


@main.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        item_name = request.form.get('item_name', '').strip()
        quantity = int(request.form.get('quantity', 0) or 0)
        unit = request.form.get('unit', 'unit').strip() or 'unit'
        minimum_level = int(request.form.get('minimum_level', 0) or 0)

        if item_name:
            db.session.add(InventoryItem(item_name=item_name, quantity=quantity, unit=unit, minimum_level=minimum_level))
            db.session.commit()
            flash('Inventory item added.', 'success')

        return redirect(url_for('main.inventory'))

    items = InventoryItem.query.order_by(InventoryItem.item_name).all()
    low_stock_items = [item for item in items if item.quantity <= item.minimum_level]
    return render_template('inventory.html', items=items, low_stock_items=low_stock_items)


@main.route('/reports')
@login_required
def reports():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    total_sales = sum(order.total_amount for order in orders)
    return render_template('reports.html', orders=orders, total_sales=total_sales)


@main.route('/order-search')
@login_required
def order_search():
    status_filter = request.args.get('status', '').strip().lower()
    table_filter = request.args.get('table', '').strip()

    query = Order.query
    if status_filter:
        query = query.filter(Order.status == status_filter)
    if table_filter:
        query = query.join(RestaurantTable).filter(RestaurantTable.table_number.ilike(f'%{table_filter}%'))

    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('order_search.html', orders=orders, status_filter=status_filter, table_filter=table_filter)


@main.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    items = order.items if hasattr(order, 'items') else []
    return render_template('order_detail.html', order=order, items=items)


@main.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status', '').strip().lower()
    if new_status in {'pending', 'preparing', 'ready', 'completed', 'cancelled'}:
        previous_status = order.status
        order.status = new_status
        db.session.commit()

        if order.customer_id and new_status in {'ready', 'completed'} and previous_status != new_status:
            message = f"Your order #{order.id} is now {new_status}."
            db.session.add(Notification(user_id=order.customer_id, message=message))
            db.session.commit()

        flash(f"Order #{order.id} status updated to {new_status}.", 'success')
    else:
        flash('Invalid status.', 'warning')
    return redirect(url_for('main.order_detail', order_id=order.id))


@main.route('/menu-management', methods=['GET', 'POST'])
@login_required
def menu_management():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_category':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            if name:
                db.session.add(Category(name=name, description=description or None))
                db.session.commit()
                flash('Category created.', 'success')
            return redirect(url_for('main.menu_management'))

        if action == 'create_product':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            price = float(request.form.get('price', 0) or 0)
            category_id = request.form.get('category_id', type=int)
            image_url = request.form.get('image_url', '').strip() or None
            available = request.form.get('available') == 'on'
            if name and category_id:
                db.session.add(Product(name=name, description=description or None, price=price, category_id=category_id, image_url=image_url, available=available))
                db.session.commit()
                flash('Product added to the menu.', 'success')
            return redirect(url_for('main.menu_management'))

        if action == 'toggle_product':
            product_id = request.form.get('product_id', type=int)
            if product_id:
                product = Product.query.get(product_id)
                if product:
                    product.available = not product.available
                    db.session.commit()
                    flash(f"{product.name} availability updated.", 'success')
            return redirect(url_for('main.menu_management'))

        if action == 'edit_product':
            product_id = request.form.get('product_id', type=int)
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            price = float(request.form.get('price', 0) or 0)
            category_id = request.form.get('category_id', type=int)
            image_url = request.form.get('image_url', '').strip() or None
            available = request.form.get('available') == 'on'
            if product_id and name and category_id:
                product = Product.query.get(product_id)
                if product:
                    product.name = name
                    product.description = description or None
                    product.price = price
                    product.category_id = category_id
                    product.image_url = image_url
                    product.available = available
                    db.session.commit()
                    flash('Product updated.', 'success')
            return redirect(url_for('main.menu_management'))

        if action == 'delete_product':
            product_id = request.form.get('product_id', type=int)
            if product_id:
                product = Product.query.get(product_id)
                if product:
                    db.session.delete(product)
                    db.session.commit()
                    flash('Product removed from the menu.', 'success')
            return redirect(url_for('main.menu_management'))

    categories = Category.query.order_by(Category.name).all()
    products = Product.query.order_by(Product.name).all()
    return render_template('menu_management.html', categories=categories, products=products)


@main.route('/database-view')
@login_required
def database_view():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    users = User.query.order_by(User.created_at.desc()).all()
    customers = Customer.query.order_by(Customer.created_at.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    products = Product.query.order_by(Product.name).all()
    offers = Offer.query.order_by(Offer.created_at.desc()).all()
    return render_template(
        'database_view.html',
        users=users,
        customers=customers,
        categories=categories,
        products=products,
        offers=offers,
    )


@main.route('/offers-management', methods=['GET', 'POST'])
@login_required
def offers_management():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_offer':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            discount = float(request.form.get('discount', 0) or 0)
            image_url = request.form.get('image_url', '').strip() or None
            active = request.form.get('active') == 'on'
            if title:
                db.session.add(Offer(title=title, description=description or None, discount=discount, image_url=image_url, active=active))
                db.session.commit()
                flash('Offer created.', 'success')
            return redirect(url_for('main.offers_management'))

        if action == 'toggle_offer':
            offer_id = request.form.get('offer_id', type=int)
            if offer_id:
                offer = Offer.query.get(offer_id)
                if offer:
                    offer.active = not offer.active
                    db.session.commit()
                    flash(f"{offer.title} status updated.", 'success')
            return redirect(url_for('main.offers_management'))

        if action == 'edit_offer':
            offer_id = request.form.get('offer_id', type=int)
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            discount = float(request.form.get('discount', 0) or 0)
            image_url = request.form.get('image_url', '').strip() or None
            active = request.form.get('active') == 'on'
            if offer_id and title:
                offer = Offer.query.get(offer_id)
                if offer:
                    offer.title = title
                    offer.description = description or None
                    offer.discount = discount
                    offer.image_url = image_url
                    offer.active = active
                    db.session.commit()
                    flash('Offer updated.', 'success')
            return redirect(url_for('main.offers_management'))

        if action == 'delete_offer':
            offer_id = request.form.get('offer_id', type=int)
            if offer_id:
                offer = Offer.query.get(offer_id)
                if offer:
                    db.session.delete(offer)
                    db.session.commit()
                    flash('Offer removed.', 'success')
            return redirect(url_for('main.offers_management'))

    offers = Offer.query.order_by(Offer.created_at.desc()).all()
    return render_template('offers_management.html', offers=offers)