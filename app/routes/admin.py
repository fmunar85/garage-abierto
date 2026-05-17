from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.product import Product, Category
from app.models.sale import Sale, SaleItem
from app.models.customer import Customer
from app.models.user import User
from app.utils import admin_required
from datetime import date, timedelta
from sqlalchemy import func
import json

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
def dashboard():
    total_products = Product.query.filter_by(active=True).count()
    low_stock_products = Product.query.filter(
        Product.stock <= Product.min_stock,
        Product.active == True
    ).order_by(Product.stock).limit(8).all()

    today = date.today()
    today_sales = Sale.query.filter(
        func.date(Sale.created_at) == today,
        Sale.status != 'cancelled'
    ).all()
    today_revenue = sum(float(s.total) for s in today_sales)

    total_customers = Customer.query.filter_by(active=True).count()
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(10).all()

    # Monthly chart data (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        m_start = (today.replace(day=1) - timedelta(days=i * 32)).replace(day=1)
        if i == 0:
            m_end = today + timedelta(days=1)
        else:
            m_end = (m_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_sales = db.session.query(func.sum(Sale.total)).filter(
            func.date(Sale.created_at) >= m_start,
            func.date(Sale.created_at) < m_end,
            Sale.status != 'cancelled'
        ).scalar() or 0
        monthly_data.append({'month': m_start.strftime('%b %Y'), 'total': float(month_sales)})

    # Top 5 products by quantity sold
    top_products = db.session.query(
        Product.name,
        func.sum(SaleItem.quantity).label('qty')
    ).join(SaleItem).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(5).all()

    # Category breakdown
    cat_data = db.session.query(
        Category.name,
        func.count(Product.id).label('count')
    ).join(Product, Product.category_id == Category.id).filter(Product.active == True).group_by(Category.id).all()

    return render_template('admin/dashboard.html',
                           total_products=total_products,
                           low_stock_products=low_stock_products,
                           today_sales_count=len(today_sales),
                           today_revenue=today_revenue,
                           total_customers=total_customers,
                           recent_sales=recent_sales,
                           monthly_data=json.dumps(monthly_data),
                           top_products=top_products,
                           cat_data=json.dumps([{'name': c.name, 'count': c.count} for c in cat_data]))


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
