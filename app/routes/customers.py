from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models.customer import Customer

customers_bp = Blueprint('customers', __name__)


@customers_bp.route('/')
@login_required
def index():
    search = request.args.get('q', '').strip()
    query = Customer.query.filter_by(active=True)
    if search:
        query = query.filter(
            db.or_(Customer.name.ilike(f'%{search}%'), Customer.phone.ilike(f'%{search}%'))
        )
    customers = query.order_by(Customer.name).all()
    return render_template('customers/index.html', customers=customers, search=search)


@customers_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def new_customer():
    if request.method == 'POST':
        c = Customer(
            name=request.form.get('name', '').strip(),
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            address=request.form.get('address', '').strip(),
            cuit_dni=request.form.get('cuit_dni', '').strip(),
            notes=request.form.get('notes', '').strip(),
        )
        if not c.name:
            flash('El nombre del cliente es obligatorio.', 'danger')
            return render_template('customers/form.html', customer=None)
        db.session.add(c)
        db.session.commit()
        flash(f'Cliente "{c.name}" creado.', 'success')
        return redirect(url_for('customers.index'))
    return render_template('customers/form.html', customer=None)


@customers_bp.route('/<int:cid>/editar', methods=['GET', 'POST'])
@login_required
def edit_customer(cid):
    c = Customer.query.get_or_404(cid)
    if request.method == 'POST':
        c.name = request.form.get('name', '').strip()
        c.phone = request.form.get('phone', '').strip()
        c.email = request.form.get('email', '').strip()
        c.address = request.form.get('address', '').strip()
        c.cuit_dni = request.form.get('cuit_dni', '').strip()
        c.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Cliente actualizado.', 'success')
        return redirect(url_for('customers.index'))
    return render_template('customers/form.html', customer=c)


@customers_bp.route('/<int:cid>/eliminar', methods=['POST'])
@login_required
def delete_customer(cid):
    c = Customer.query.get_or_404(cid)
    c.active = False
    db.session.commit()
    flash(f'Cliente "{c.name}" eliminado.', 'warning')
    return redirect(url_for('customers.index'))
