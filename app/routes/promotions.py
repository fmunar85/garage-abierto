from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models.promotion import BankPromotion
from app.utils import admin_required
from datetime import date

promotions_bp = Blueprint('promotions', __name__)

BANKS = [
    'Banco Nación', 'Banco Provincia', 'BBVA', 'Santander', 'Galicia',
    'HSBC', 'Macro', 'ICBC', 'Brubank', 'Naranja X', 'Mercado Pago',
    'Ualá', 'Banco Ciudad', 'Credicoop', 'Personal Pay', 'Otro'
]
CARDS = ['Todas', 'VISA', 'Mastercard', 'AMEX', 'Cabal', 'Naranja', 'Maestro']


@promotions_bp.route('/')
@login_required
def index():
    promos = BankPromotion.query.order_by(BankPromotion.valid_until.desc()).all()
    today = date.today()
    return render_template('promotions/index.html', promos=promos, today=today)


@promotions_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def new_promotion():
    if request.method == 'POST':
        promo = BankPromotion(
            bank=request.form['bank'].strip(),
            card_type=request.form.get('card_type', '').strip(),
            installments=int(request.form.get('installments', 1)),
            interest_rate=float(request.form.get('interest_rate', 0) or 0),
            discount_pct=float(request.form.get('discount_pct', 0) or 0),
            valid_from=date.fromisoformat(request.form['valid_from']),
            valid_until=date.fromisoformat(request.form['valid_until']),
            description=request.form.get('description', '').strip(),
            active=bool(request.form.get('active')),
        )
        db.session.add(promo)
        db.session.commit()
        flash('Promoción creada correctamente.', 'success')
        return redirect(url_for('promotions.index'))
    return render_template('promotions/form.html', promo=None, banks=BANKS, cards=CARDS,
                           today=date.today().isoformat())


@promotions_bp.route('/<int:pid>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_promotion(pid):
    promo = BankPromotion.query.get_or_404(pid)
    if request.method == 'POST':
        promo.bank = request.form['bank'].strip()
        promo.card_type = request.form.get('card_type', '').strip()
        promo.installments = int(request.form.get('installments', 1))
        promo.interest_rate = float(request.form.get('interest_rate', 0) or 0)
        promo.discount_pct = float(request.form.get('discount_pct', 0) or 0)
        promo.valid_from = date.fromisoformat(request.form['valid_from'])
        promo.valid_until = date.fromisoformat(request.form['valid_until'])
        promo.description = request.form.get('description', '').strip()
        promo.active = bool(request.form.get('active'))
        db.session.commit()
        flash('Promoción actualizada.', 'success')
        return redirect(url_for('promotions.index'))
    return render_template('promotions/form.html', promo=promo, banks=BANKS, cards=CARDS,
                           today=date.today().isoformat())


@promotions_bp.route('/<int:pid>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_promotion(pid):
    promo = BankPromotion.query.get_or_404(pid)
    promo.active = not promo.active
    db.session.commit()
    flash(f'Promoción {"activada" if promo.active else "desactivada"}.', 'success')
    return redirect(url_for('promotions.index'))


@promotions_bp.route('/<int:pid>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_promotion(pid):
    promo = BankPromotion.query.get_or_404(pid)
    db.session.delete(promo)
    db.session.commit()
    flash('Promoción eliminada.', 'warning')
    return redirect(url_for('promotions.index'))
