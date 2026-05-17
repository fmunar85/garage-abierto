from app import db
from datetime import datetime, timezone


class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    subtotal = db.Column(db.Numeric(12, 2), default=0)
    discount = db.Column(db.Numeric(5, 2), default=0)   # percentage 0-100
    total = db.Column(db.Numeric(12, 2), default=0)

    payment_method = db.Column(db.String(30), default='efectivo')  # efectivo | tarjeta | transferencia | cuenta_corriente
    status = db.Column(db.String(20), default='completed')          # completed | pending | cancelled
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship('SaleItem', backref='sale', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Sale #{self.id}>'


class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)

    def __repr__(self):
        return f'<SaleItem sale={self.sale_id} product={self.product_id}>'
