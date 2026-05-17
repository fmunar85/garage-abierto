from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models.supplier import Supplier
from app.utils import admin_required

suppliers_bp = Blueprint('suppliers', __name__)


@suppliers_bp.route('/')
@login_required
def index():
    search = request.args.get('q', '').strip()
    query = Supplier.query
    if search:
        query = query.filter(Supplier.name.ilike(f'%{search}%'))
    suppliers = query.order_by(Supplier.name).all()
    return render_template('suppliers/index.html', suppliers=suppliers, search=search)


@suppliers_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def new_supplier():
    if request.method == 'POST':
        s = Supplier(
            name=request.form.get('name', '').strip(),
            contact_name=request.form.get('contact_name', '').strip(),
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            address=request.form.get('address', '').strip(),
            cuit=request.form.get('cuit', '').strip(),
            notes=request.form.get('notes', '').strip(),
        )
        if not s.name:
            flash('El nombre del proveedor es obligatorio.', 'danger')
            return render_template('suppliers/form.html', supplier=None)
        db.session.add(s)
        db.session.commit()
        flash(f'Proveedor "{s.name}" creado.', 'success')
        return redirect(url_for('suppliers.index'))
    return render_template('suppliers/form.html', supplier=None)


@suppliers_bp.route('/<int:sid>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_supplier(sid):
    s = Supplier.query.get_or_404(sid)
    if request.method == 'POST':
        s.name = request.form.get('name', '').strip()
        s.contact_name = request.form.get('contact_name', '').strip()
        s.phone = request.form.get('phone', '').strip()
        s.email = request.form.get('email', '').strip()
        s.address = request.form.get('address', '').strip()
        s.cuit = request.form.get('cuit', '').strip()
        s.notes = request.form.get('notes', '').strip()
        s.active = 'active' in request.form
        db.session.commit()
        flash('Proveedor actualizado.', 'success')
        return redirect(url_for('suppliers.index'))
    return render_template('suppliers/form.html', supplier=s)


@suppliers_bp.route('/<int:sid>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_supplier(sid):
    s = Supplier.query.get_or_404(sid)
    s.active = False
    db.session.commit()
    flash(f'Proveedor "{s.name}" desactivado.', 'warning')
    return redirect(url_for('suppliers.index'))
