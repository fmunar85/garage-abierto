from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models.employee import Employee
from app.utils import admin_required
from datetime import date

employees_bp = Blueprint('employees', __name__)


@employees_bp.route('/')
@login_required
@admin_required
def index():
    search = request.args.get('q', '').strip()
    query = Employee.query.filter_by(active=True)
    if search:
        query = query.filter(Employee.name.ilike(f'%{search}%'))
    employees = query.order_by(Employee.name).all()
    total_salary = sum(float(e.salary) for e in employees)
    return render_template('employees/index.html', employees=employees, search=search, total_salary=total_salary)


@employees_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def new_employee():
    if request.method == 'POST':
        hire_str = request.form.get('hire_date', '')
        hire_date = date.fromisoformat(hire_str) if hire_str else None
        e = Employee(
            name=request.form.get('name', '').strip(),
            position=request.form.get('position', '').strip(),
            salary=float(request.form.get('salary', 0) or 0),
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            dni=request.form.get('dni', '').strip(),
            address=request.form.get('address', '').strip(),
            hire_date=hire_date,
            notes=request.form.get('notes', '').strip(),
        )
        if not e.name:
            flash('El nombre del empleado es obligatorio.', 'danger')
            return render_template('employees/form.html', employee=None)
        db.session.add(e)
        db.session.commit()
        flash(f'Empleado "{e.name}" agregado.', 'success')
        return redirect(url_for('employees.index'))
    return render_template('employees/form.html', employee=None)


@employees_bp.route('/<int:eid>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_employee(eid):
    e = Employee.query.get_or_404(eid)
    if request.method == 'POST':
        hire_str = request.form.get('hire_date', '')
        e.name = request.form.get('name', '').strip()
        e.position = request.form.get('position', '').strip()
        e.salary = float(request.form.get('salary', 0) or 0)
        e.phone = request.form.get('phone', '').strip()
        e.email = request.form.get('email', '').strip()
        e.dni = request.form.get('dni', '').strip()
        e.address = request.form.get('address', '').strip()
        e.hire_date = date.fromisoformat(hire_str) if hire_str else e.hire_date
        e.notes = request.form.get('notes', '').strip()
        e.active = 'active' in request.form
        db.session.commit()
        flash('Empleado actualizado.', 'success')
        return redirect(url_for('employees.index'))
    return render_template('employees/form.html', employee=e)


@employees_bp.route('/<int:eid>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_employee(eid):
    e = Employee.query.get_or_404(eid)
    e.active = False
    db.session.commit()
    flash(f'Empleado "{e.name}" dado de baja.', 'warning')
    return redirect(url_for('employees.index'))
