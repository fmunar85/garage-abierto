from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.product import Product, Category
from app.models.sale import Sale, SaleItem
from app.models.customer import Customer
from app.models.user import User
from app.models.promotion import BankPromotion
from app.models.company import CompanySettings
from app.utils import admin_required
from datetime import date, timedelta
from sqlalchemy import func
import json
import os

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
def dashboard():
    today = date.today()
    month_start = today.replace(day=1)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
    prev_month_end = month_start

    # ── KPIs básicos ──────────────────────────────────────────
    total_products = Product.query.filter_by(active=True).count()
    total_customers = Customer.query.filter_by(active=True).count()

    low_stock_products = Product.query.filter(
        Product.stock <= Product.min_stock,
        Product.active == True
    ).order_by(Product.stock).all()

    out_of_stock_count = sum(1 for p in low_stock_products if p.stock == 0)

    # Ventas hoy
    today_sales = Sale.query.filter(
        func.date(Sale.created_at) == today,
        Sale.status != 'cancelled'
    ).all()
    today_revenue = sum(float(s.total) for s in today_sales)
    today_cost = sum(
        float(si.unit_price) * si.quantity * 0  # we'll calc from products
        for s in today_sales for si in s.items
    )

    # Ventas mes actual
    month_sales_q = Sale.query.filter(
        func.date(Sale.created_at) >= month_start,
        Sale.status != 'cancelled'
    ).all()
    month_revenue = sum(float(s.total) for s in month_sales_q)

    # Ventas mes anterior (para comparativa)
    prev_month_revenue_raw = db.session.query(func.sum(Sale.total)).filter(
        func.date(Sale.created_at) >= prev_month_start,
        func.date(Sale.created_at) < prev_month_end,
        Sale.status != 'cancelled'
    ).scalar() or 0
    prev_month_revenue = float(prev_month_revenue_raw)

    month_delta_pct = 0
    if prev_month_revenue > 0:
        month_delta_pct = round(((month_revenue - prev_month_revenue) / prev_month_revenue) * 100, 1)

    # Ticket promedio del mes
    avg_ticket = (month_revenue / len(month_sales_q)) if month_sales_q else 0

    # Margen bruto estimado del mes (precio venta - costo)
    gross_profit = 0
    for s in month_sales_q:
        for si in s.items:
            cost = float(si.product.cost_price or 0)
            gross_profit += (float(si.unit_price) - cost) * si.quantity
    gross_margin_pct = round((gross_profit / month_revenue * 100), 1) if month_revenue > 0 else 0

    # ── Ventas por método de pago (mes actual) ────────────────
    payment_data = db.session.query(
        Sale.payment_method,
        func.count(Sale.id).label('cnt'),
        func.sum(Sale.total).label('total')
    ).filter(
        func.date(Sale.created_at) >= month_start,
        Sale.status != 'cancelled'
    ).group_by(Sale.payment_method).all()

    # ── Últimas 30 días - gráfico diario ─────────────────────
    daily_data = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        rev = db.session.query(func.sum(Sale.total)).filter(
            func.date(Sale.created_at) == d,
            Sale.status != 'cancelled'
        ).scalar() or 0
        daily_data.append({'day': d.strftime('%d/%m'), 'total': float(rev)})

    # ── Últimos 6 meses ───────────────────────────────────────
    monthly_data = []
    for i in range(5, -1, -1):
        m_start = (today.replace(day=1) - timedelta(days=i * 32)).replace(day=1)
        m_end = (m_start.replace(day=28) + timedelta(days=4)).replace(day=1) if i > 0 else today + timedelta(days=1)
        rev = db.session.query(func.sum(Sale.total)).filter(
            func.date(Sale.created_at) >= m_start,
            func.date(Sale.created_at) < m_end,
            Sale.status != 'cancelled'
        ).scalar() or 0
        qty = db.session.query(func.count(Sale.id)).filter(
            func.date(Sale.created_at) >= m_start,
            func.date(Sale.created_at) < m_end,
            Sale.status != 'cancelled'
        ).scalar() or 0
        monthly_data.append({'month': m_start.strftime('%b %y'), 'total': float(rev), 'qty': qty})

    # ── Top 8 productos por facturación (mes) ────────────────
    top_products = db.session.query(
        Product.name,
        Product.sku,
        func.sum(SaleItem.quantity).label('qty'),
        func.sum(SaleItem.subtotal).label('revenue')
    ).join(SaleItem).join(Sale).filter(
        func.date(Sale.created_at) >= month_start,
        Sale.status != 'cancelled'
    ).group_by(Product.id).order_by(func.sum(SaleItem.subtotal).desc()).limit(8).all()

    # Si no hay del mes, mostrar histórico
    if not top_products:
        top_products = db.session.query(
            Product.name,
            Product.sku,
            func.sum(SaleItem.quantity).label('qty'),
            func.sum(SaleItem.subtotal).label('revenue')
        ).join(SaleItem).group_by(Product.id).order_by(func.sum(SaleItem.subtotal).desc()).limit(8).all()

    # ── Ventas recientes ──────────────────────────────────────
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(8).all()

    # ── Promociones vigentes ──────────────────────────────────
    active_promos = BankPromotion.query.filter(
        BankPromotion.active == True,
        BankPromotion.valid_from <= today,
        BankPromotion.valid_until >= today
    ).all()

    return render_template('admin/dashboard.html',
        total_products=total_products,
        total_customers=total_customers,
        low_stock_products=low_stock_products[:8],
        low_stock_count=len(low_stock_products),
        out_of_stock_count=out_of_stock_count,
        today_sales_count=len(today_sales),
        today_revenue=today_revenue,
        month_revenue=month_revenue,
        prev_month_revenue=prev_month_revenue,
        month_delta_pct=month_delta_pct,
        avg_ticket=avg_ticket,
        gross_margin_pct=gross_margin_pct,
        gross_profit=gross_profit,
        payment_data=payment_data,
        daily_data=json.dumps(daily_data),
        monthly_data=json.dumps(monthly_data),
        top_products=top_products,
        recent_sales=recent_sales,
        active_promos=active_promos,
    )


@admin_bp.route('/usuarios')
@login_required
@admin_required
def users():
    users_list = User.query.order_by(User.name).all()
    return render_template('admin/users.html', users=users_list)


@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'seller')
        if not name or not email or not password:
            flash('Completá todos los campos obligatorios.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Ya existe un usuario con ese email.', 'danger')
        else:
            u = User(name=name, email=email, role=role)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash(f'Usuario {name} creado correctamente.', 'success')
            return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', user=None)


@admin_bp.route('/usuarios/<int:uid>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(uid):
    u = User.query.get_or_404(uid)
    if request.method == 'POST':
        u.name = request.form.get('name', '').strip()
        u.role = request.form.get('role', 'seller')
        u.active = 'active' in request.form
        new_pw = request.form.get('password', '')
        if new_pw:
            u.set_password(new_pw)
        db.session.commit()
        flash('Usuario actualizado.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', user=u)


@admin_bp.route('/usuarios/<int:uid>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_user(uid):
    u = User.query.get_or_404(uid)
    if u.id == current_user.id:
        flash('No podés eliminar tu propia cuenta.', 'danger')
    else:
        db.session.delete(u)
        db.session.commit()
        flash('Usuario eliminado.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/actualizar-imagenes', methods=['POST'])
@login_required
@admin_required
def update_images():
    U = 'https://images.unsplash.com/photo'
    images = {
        'SAN001': f'{U}-1585771724684-38269d6639fd?w=600&q=80&fit=crop',
        'SAN002': f'{U}-1552321554-5fefe8c9ef14?w=600&q=80&fit=crop',
        'SAN003': f'{U}-1620626011761-99316d1814b4?w=600&q=80&fit=crop',
        'SAN004': f'{U}-1552321554-5fefe8c9ef14?w=600&q=80&fit=crop',
        'SAN005': f'{U}-1585771724684-38269d6639fd?w=600&q=80&fit=crop',
        'SAN006': f'{U}-1620626011761-99316d1814b4?w=600&q=80&fit=crop',
        'SAN007': f'{U}-1552321554-5fefe8c9ef14?w=600&q=80&fit=crop',
        'SAN008': f'{U}-1585771724684-38269d6639fd?w=600&q=80&fit=crop',
        'GRI001': f'{U}-1558618666-fcd25c85cd64?w=600&q=80&fit=crop',
        'GRI002': f'{U}-1600566752355-35792fbb5b59?w=600&q=80&fit=crop',
        'GRI003': f'{U}-1518455374-6e9e4a5aafd5?w=600&q=80&fit=crop',
        'GRI004': f'{U}-1524484485831-a92ffc0de03f?w=600&q=80&fit=crop',
        'GRI005': f'{U}-1601924428597-a5af478e5f1c?w=600&q=80&fit=crop',
        'GRI006': f'{U}-1558618666-fcd25c85cd64?w=600&q=80&fit=crop',
        'GRI007': f'{U}-1524484485831-a92ffc0de03f?w=600&q=80&fit=crop',
        'GRI008': f'{U}-1601924428597-a5af478e5f1c?w=600&q=80&fit=crop',
        'GRI009': f'{U}-1518455374-6e9e4a5aafd5?w=600&q=80&fit=crop',
        'GRI010': f'{U}-1600566752355-35792fbb5b59?w=600&q=80&fit=crop',
        'BAU001': f'{U}-1604709177225-055f99402ea3?w=600&q=80&fit=crop',
        'BAU002': f'{U}-1507652313519-d4e9174996dd?w=600&q=80&fit=crop',
        'BAU003': f'{U}-1552566626-52f8b828add9?w=600&q=80&fit=crop',
        'BAU004': f'{U}-1556909114-f6e7ad7d3136?w=600&q=80&fit=crop',
        'BAU005': f'{U}-1552566626-52f8b828add9?w=600&q=80&fit=crop',
        'BAU006': f'{U}-1604709177225-055f99402ea3?w=600&q=80&fit=crop',
        'BAU007': f'{U}-1556909114-f6e7ad7d3136?w=600&q=80&fit=crop',
        'BAU008': f'{U}-1507652313519-d4e9174996dd?w=600&q=80&fit=crop',
        'ACC001': f'{U}-1589939705384-5185137a7f0f?w=600&q=80&fit=crop',
        'ACC002': f'{U}-1598300042738-d4e4e9d54cb3?w=600&q=80&fit=crop',
        'ACC003': f'{U}-1589939705384-5185137a7f0f?w=600&q=80&fit=crop',
        'ACC004': f'{U}-1598300042738-d4e4e9d54cb3?w=600&q=80&fit=crop',
        'ACC005': f'{U}-1583845112203-29329902332e?w=600&q=80&fit=crop',
        'ACC006': f'{U}-1589939705384-5185137a7f0f?w=600&q=80&fit=crop',
        'ACC007': f'{U}-1598300042738-d4e4e9d54cb3?w=600&q=80&fit=crop',
        'ACC008': f'{U}-1583845112203-29329902332e?w=600&q=80&fit=crop',
        'ACC009': f'{U}-1589939705384-5185137a7f0f?w=600&q=80&fit=crop',
        'ACC010': f'{U}-1598300042738-d4e4e9d54cb3?w=600&q=80&fit=crop',
        'MAM001': f'{U}-1552566626-52f8b828add9?w=600&q=80&fit=crop',
        'MAM002': f'{U}-1600566752355-35792fbb5b59?w=600&q=80&fit=crop',
        'MAM003': f'{U}-1552566626-52f8b828add9?w=600&q=80&fit=crop',
        'MAM004': f'{U}-1545552696-f047cb5a9e51?w=600&q=80&fit=crop',
        'MAM005': f'{U}-1545552696-f047cb5a9e51?w=600&q=80&fit=crop',
        'MAM006': f'{U}-1600566752355-35792fbb5b59?w=600&q=80&fit=crop',
        'MAM007': f'{U}-1552566626-52f8b828add9?w=600&q=80&fit=crop',
        'MAM008': f'{U}-1545552696-f047cb5a9e51?w=600&q=80&fit=crop',
        'MUE001': f'{U}-1556909114-f6e7ad7d3136?w=600&q=80&fit=crop',
        'MUE002': f'{U}-1507652313519-d4e9174996dd?w=600&q=80&fit=crop',
        'MUE003': f'{U}-1583845112203-29329902332e?w=600&q=80&fit=crop',
        'MUE004': f'{U}-1556909114-f6e7ad7d3136?w=600&q=80&fit=crop',
        'MUE005': f'{U}-1507652313519-d4e9174996dd?w=600&q=80&fit=crop',
        'MUE006': f'{U}-1583845112203-29329902332e?w=600&q=80&fit=crop',
        'MUE007': f'{U}-1556909114-f6e7ad7d3136?w=600&q=80&fit=crop',
        'MUE008': f'{U}-1507652313519-d4e9174996dd?w=600&q=80&fit=crop',
        'CAL001': f'{U}-1517581177682-a085bb7ffb15?w=600&q=80&fit=crop',
        'CAL002': f'{U}-1517581177682-a085bb7ffb15?w=600&q=80&fit=crop',
        'CAL003': f'{U}-1518455374-6e9e4a5aafd5?w=600&q=80&fit=crop',
        'CAL004': f'{U}-1517581177682-a085bb7ffb15?w=600&q=80&fit=crop',
        'CAL005': f'{U}-1583845112203-29329902332e?w=600&q=80&fit=crop',
        'CAL006': f'{U}-1517581177682-a085bb7ffb15?w=600&q=80&fit=crop',
        'REV001': f'{U}-1545552696-f047cb5a9e51?w=600&q=80&fit=crop',
        'REV002': f'{U}-1600566752355-35792fbb5b59?w=600&q=80&fit=crop',
        'REV003': f'{U}-1545552696-f047cb5a9e51?w=600&q=80&fit=crop',
        'REV004': f'{U}-1600566752355-35792fbb5b59?w=600&q=80&fit=crop',
        'REV005': f'{U}-1545552696-f047cb5a9e51?w=600&q=80&fit=crop',
        'REV006': f'{U}-1600566752355-35792fbb5b59?w=600&q=80&fit=crop',
        'REV007': f'{U}-1545552696-f047cb5a9e51?w=600&q=80&fit=crop',
        'REV008': f'{U}-1600566752355-35792fbb5b59?w=600&q=80&fit=crop',
    }
    n = 0
    for sku, url in images.items():
        p = Product.query.filter_by(sku=sku).first()
        if p:
            p.image_url = url
            n += 1
    db.session.commit()
    flash(f'✅ {n} imágenes actualizadas correctamente.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/cloudinary-info')
@login_required
@admin_required
def cloudinary_info():
    """Página de ayuda para configurar Cloudinary en Railway."""
    configured = all(os.environ.get(k) for k in (
        'CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET'
    ))
    return render_template('admin/cloudinary_info.html', configured=configured)


@admin_bp.route('/empresa', methods=['GET', 'POST'])
@login_required
@admin_required
def company_settings():
    """Configuración de marca / white-label de la empresa."""
    settings = CompanySettings.get()
    if request.method == 'POST':
        settings.company_name  = request.form.get('company_name', '').strip() or settings.company_name
        settings.tagline       = request.form.get('tagline', '').strip()
        settings.logo_url      = request.form.get('logo_url', '').strip() or None
        settings.primary_color = request.form.get('primary_color', '#1a5fb4')
        settings.accent_color  = request.form.get('accent_color', '#2ec4a9')
        settings.address       = request.form.get('address', '').strip() or None
        settings.phone         = request.form.get('phone', '').strip() or None
        settings.whatsapp      = request.form.get('whatsapp', '').strip() or None
        settings.email         = request.form.get('email', '').strip() or None
        settings.website       = request.form.get('website', '').strip() or None
        db.session.commit()
        flash('✅ Configuración de empresa guardada correctamente.', 'success')
        return redirect(url_for('admin.company_settings'))
    return render_template('admin/company.html', settings=settings)
