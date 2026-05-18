from app import db
from datetime import datetime, timezone, date


class BankPromotion(db.Model):
    __tablename__ = 'bank_promotions'

    id = db.Column(db.Integer, primary_key=True)
    bank = db.Column(db.String(100), nullable=False)         # Banco Nación, BBVA, etc.
    card_type = db.Column(db.String(50), default='')          # VISA, MC, AMEX, Todas
    installments = db.Column(db.Integer, default=1)           # Cuotas
    interest_rate = db.Column(db.Numeric(5, 2), default=0)   # % recargo (0 = sin interés)
    discount_pct = db.Column(db.Numeric(5, 2), default=0)    # % descuento directo
    valid_from = db.Column(db.Date, nullable=False, default=date.today)
    valid_until = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, default='')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def is_current(self):
        today = date.today()
        return self.active and self.valid_from <= today <= self.valid_until

    @property
    def label(self):
        parts = []
        if self.installments > 1:
            parts.append(f'{self.installments} cuotas')
            if float(self.interest_rate) == 0:
                parts[-1] += ' sin interés'
            else:
                parts[-1] += f' ({self.interest_rate}% recargo)'
        if float(self.discount_pct) > 0:
            parts.append(f'{self.discount_pct}% descuento')
        return ' | '.join(parts) if parts else 'Promoción'

    def __repr__(self):
        return f'<BankPromotion {self.bank} {self.installments}c>'
