from app import db
from datetime import datetime, timezone


class StockMovement(db.Model):
    __tablename__ = 'stock_movements'

    id         = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 'sale' | 'adjustment' | 'reception' | 'count' | 'correction' | 'initial'
    type       = db.Column(db.String(30), nullable=False, default='adjustment')
    qty_before = db.Column(db.Integer, nullable=False, default=0)
    qty_change = db.Column(db.Integer, nullable=False, default=0)   # + entrada / - salida
    qty_after  = db.Column(db.Integer, nullable=False, default=0)
    reason     = db.Column(db.String(300))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship('Product', backref=db.backref('movements', lazy='dynamic', order_by='StockMovement.created_at.desc()'))
    user    = db.relationship('User')

    # Labels amigables
    TYPE_LABELS = {
        'sale':       ('Venta',            'bi-receipt',           'text-primary'),
        'adjustment': ('Ajuste manual',    'bi-sliders',           'text-warning'),
        'reception':  ('Recepción',        'bi-box-arrow-in-down', 'text-success'),
        'count':      ('Conteo físico',    'bi-clipboard-check',   'text-info'),
        'correction': ('Corrección',       'bi-pencil-square',     'text-secondary'),
        'initial':    ('Stock inicial',    'bi-play-circle',       'text-muted'),
    }

    @property
    def label(self):
        return self.TYPE_LABELS.get(self.type, (self.type, 'bi-circle', 'text-muted'))

    def __repr__(self):
        return f'<StockMovement {self.type} {self.qty_change:+d} on product {self.product_id}>'
