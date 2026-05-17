from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.product import Product, Category
from app.models.supplier import Supplier
from app.utils import admin_required
from werkzeug.utils import secure_filename
import os
import uuid

inventory_bp = Blueprint('inventory', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        return filename
    return None


@inventory_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    category_id = request.args.get('cat', type=int)
    stock_filter = request.args.get('stock', '')
    active_filter = request.args.get('activo', '1')

    query = Product.query
    if active_filter == '0':
        query = query.filter_by(active=False)
    else:
        query = query.filter_by(active=True)

    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%'),
                Product.brand.ilike(f'%{search}%'),
            )
        )
    if category_id:
        query = query.filter_by(category_id=category_id)
    if stock_filter == 'low':
        query = query.filter(Product.stock <= Product.min_stock)
    elif stock_filter == 'out':
        query = query.filter(Product.stock == 0)

    products = query.order_by(Product.category_id, Product.name).paginate(page=page, per_page=24, error_out=False)
    categories = Category.query.order_by(Category.name).all()

    return render_template('inventory/index.html',
                           products=products,
                           categories=categories,
                           search=search,
                           category_id=category_id,
                           stock_filter=stock_filter,
                           active_filter=active_filter)


@inventory_bp.route('/producto/<int:pid>')
@login_required
def product_detail(pid):
    product = Product.query.get_or_404(pid)
    recent_items = product.sale_items.order_by(db.text('id desc')).limit(10).all()
    return render_template('inventory/detail.html', product=product, recent_items=recent_items)


@inventory_bp.route('/producto/nuevo', methods=['GET', 'POST'])
@login_required
def new_product():
    categories = Category.query.order_by(Category.name).all()
    suppliers = Supplier.query.filter_by(active=True).order_by(Supplier.name).all()
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip().upper()
        if not sku or not request.form.get('name') or not request.form.get('price'):
            flash('SKU, nombre y precio son obligatorios.', 'danger')
            return render_template('inventory/form.html', product=None, categories=categories, suppliers=suppliers)
        if Product.query.filter_by(sku=sku).first():
            flash(f'El SKU {sku} ya existe.', 'danger')
            return render_template('inventory/form.html', product=None, categories=categories, suppliers=suppliers)

        image_filename = None
        file = request.files.get('image_file')
        image_filename = save_uploaded_image(file)
        if not image_filename:
            image_filename = request.form.get('image_url') or None

        p = Product(
            sku=sku,
            name=request.form.get('name', '').strip(),
            description=request.form.get('description', '').strip(),
            brand=request.form.get('brand', '').strip(),
            category_id=request.form.get('category_id') or None,
            supplier_id=request.form.get('supplier_id') or None,
            price=float(request.form.get('price', 0)),
            cost_price=float(request.form.get('cost_price', 0)),
            stock=int(request.form.get('stock', 0)),
            min_stock=int(request.form.get('min_stock', 5)),
            image_url=image_filename,
            featured='featured' in request.form,
        )
        db.session.add(p)
        db.session.commit()
        flash(f'Producto "{p.name}" creado correctamente.', 'success')
        return redirect(url_for('inventory.product_detail', pid=p.id))
    return render_template('inventory/form.html', product=None, categories=categories, suppliers=suppliers)


@inventory_bp.route('/producto/<int:pid>/editar', methods=['GET', 'POST'])
@login_required
def edit_product(pid):
    product = Product.query.get_or_404(pid)
    categories = Category.query.order_by(Category.name).all()
    suppliers = Supplier.query.filter_by(active=True).order_by(Supplier.name).all()
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip().upper()
        existing = Product.query.filter_by(sku=sku).first()
        if existing and existing.id != pid:
            flash(f'El SKU {sku} ya pertenece a otro producto.', 'danger')
            return render_template('inventory/form.html', product=product, categories=categories, suppliers=suppliers)

        file = request.files.get('image_file')
        new_img = save_uploaded_image(file)
        if new_img:
            product.image_url = new_img
        elif request.form.get('image_url'):
            product.image_url = request.form.get('image_url')

        product.sku = sku
        product.name = request.form.get('name', '').strip()
        product.description = request.form.get('description', '').strip()
        product.brand = request.form.get('brand', '').strip()
        product.category_id = request.form.get('category_id') or None
        product.supplier_id = request.form.get('supplier_id') or None
        product.price = float(request.form.get('price', 0))
        product.cost_price = float(request.form.get('cost_price', 0))
        product.min_stock = int(request.form.get('min_stock', 5))
        product.active = 'active' in request.form
        product.featured = 'featured' in request.form
        db.session.commit()
        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('inventory.product_detail', pid=product.id))
    return render_template('inventory/form.html', product=product, categories=categories, suppliers=suppliers)


@inventory_bp.route('/producto/<int:pid>/stock', methods=['POST'])
@login_required
def adjust_stock(pid):
    product = Product.query.get_or_404(pid)
    amount = int(request.form.get('amount', 0))
    operation = request.form.get('operation', 'add')
    if operation == 'add':
        product.stock += amount
        flash(f'Se agregaron {amount} unidades. Stock actual: {product.stock}', 'success')
    elif operation == 'subtract':
        if product.stock < amount:
            flash('No hay suficiente stock para esa cantidad.', 'danger')
            return redirect(url_for('inventory.product_detail', pid=pid))
        product.stock -= amount
        flash(f'Se retiraron {amount} unidades. Stock actual: {product.stock}', 'success')
    elif operation == 'set':
        product.stock = amount
        flash(f'Stock ajustado a {amount} unidades.', 'success')
    db.session.commit()
    return redirect(url_for('inventory.product_detail', pid=pid))


@inventory_bp.route('/producto/<int:pid>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_product(pid):
    product = Product.query.get_or_404(pid)
    product.active = False
    db.session.commit()
    flash(f'Producto "{product.name}" dado de baja.', 'warning')
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/categorias')
@login_required
@admin_required
def categories():
    cats = Category.query.order_by(Category.name).all()
    return render_template('inventory/categories.html', categories=cats)


@inventory_bp.route('/categorias/nueva', methods=['POST'])
@login_required
@admin_required
def new_category():
    name = request.form.get('name', '').strip()
    icon = request.form.get('icon', 'bi-box').strip()
    color = request.form.get('color', '#2196F3').strip()
    if name and not Category.query.filter_by(name=name).first():
        cat = Category(name=name, icon=icon, color=color)
        db.session.add(cat)
        db.session.commit()
        flash(f'Categoría "{name}" creada.', 'success')
    else:
        flash('Nombre inválido o ya existe esa categoría.', 'danger')
    return redirect(url_for('inventory.categories'))
