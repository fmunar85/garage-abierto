from app import db
from datetime import datetime, timezone


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    cuit_dni = db.Column(db.String(20))
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sales = db.relationship('Sale', backref='customer', lazy='dynamic')

    @property
    def total_purchases(self):
        try:
            return sum(float(s.total) for s in self.sales if s.status != 'cancelled')
        except Exception:
            return 0

    def __repr__(self):
        return f'<Customer {self.name}>'
