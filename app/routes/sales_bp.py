from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.product import Product, Category
from app.models.sale import Sale, SaleItem
from app.models.customer import Customer
from app.utils import admin_required

sales_bp = Blueprint('sales', __name__)


@sales_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    payment = request.args.get('payment', '')
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')

    query = Sale.query
    if status:
        query = query.filter_by(status=status)
    if payment:
        query = query.filter_by(payment_method=payment)
    if date_from:
        query = query.filter(db.func.date(Sale.created_at) >= date_from)
    if date_to:
        query = query.filter(db.func.date(Sale.created_at) <= date_to)

    sales = query.order_by(Sale.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('sales/index.html', sales=sales, status=status, payment=payment,
                           date_from=date_from, date_to=date_to)


@sales_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def new_sale():
    customers = Customer.query.filter_by(active=True).order_by(Customer.name).all()
    if request.method == 'POST':
        import json as _json
        items_json = request.form.get('items_json', '[]')
        try:
            items_data = _json.loads(items_json)
        except Exception:
            flash('Error al procesar los artículos de la venta.', 'danger')
            return redirect(url_for('sales.new_sale'))

        if not items_data:
            flash('La venta debe tener al menos un artículo.', 'danger')
            return redirect(url_for('sales.new_sale'))

        customer_id = request.form.get('customer_id') or None
        payment_method = request.form.get('payment_method', 'efectivo')
        discount = float(request.form.get('discount', 0) or 0)
        notes = request.form.get('notes', '').strip()

        subtotal = 0.0
        for item in items_data:
            subtotal += float(item['price']) * int(item['qty'])
        total = subtotal * (1 - discount / 100)

        sale = Sale(
            customer_id=customer_id,
            user_id=current_user.id,
            subtotal=round(subtotal, 2),
            discount=discount,
            total=round(total, 2),
            payment_method=payment_method,
            status='completed',
            notes=notes,
        )
        db.session.add(sale)
        db.session.flush()

        for item in items_data:
            p = Product.query.get(int(item['id']))
            if not p:
                continue
            qty = int(item['qty'])
            price = float(item['price'])
            si = SaleItem(
                sale_id=sale.id,
                product_id=p.id,
                quantity=qty,
                unit_price=price,
                subtotal=round(price * qty, 2),
            )
            p.stock = max(0, p.stock - qty)
            db.session.add(si)

        db.session.commit()
        flash(f'Venta #{sale.id} registrada por ${total:,.0f}.'.replace(',', '.'), 'success')
        return redirect(url_for('sales.sale_detail', sid=sale.id))

    return render_template('sales/new.html', customers=customers)


@sales_bp.route('/<int:sid>')
@login_required
def sale_detail(sid):
    sale = Sale.query.get_or_404(sid)
    return render_template('sales/detail.html', sale=sale)


@sales_bp.route('/<int:sid>/cancelar', methods=['POST'])
@login_required
@admin_required
def cancel_sale(sid):
    sale = Sale.query.get_or_404(sid)
    if sale.status == 'completed':
        # Restore stock
        for item in sale.items:
            item.product.stock += item.quantity
        sale.status = 'cancelled'
        db.session.commit()
        flash(f'Venta #{sid} cancelada y stock restaurado.', 'warning')
    else:
        flash('La venta no puede cancelarse en su estado actual.', 'danger')
    return redirect(url_for('sales.sale_detail', sid=sid))


@sales_bp.route('/buscar-productos')
@login_required
def search_products():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    products = Product.query.filter(
        Product.active == True,
        Product.stock > 0,
        db.or_(
            Product.name.ilike(f'%{q}%'),
            Product.sku.ilike(f'%{q}%'),
            Product.brand.ilike(f'%{q}%'),
        )
    ).limit(15).all()
    return jsonify([{
        'id': p.id,
        'sku': p.sku,
        'name': p.name,
        'brand': p.brand or '',
        'price': float(p.price),
        'stock': p.stock,
        'image': p.image_src or '',
    } for p in products])
