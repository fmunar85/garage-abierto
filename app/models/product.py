from app import db
from datetime import datetime, timezone


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    icon = db.Column(db.String(50), default='bi-box')
    color = db.Column(db.String(20), default='#2196F3')

    products = db.relationship('Product', backref='category_obj', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    brand = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)

    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)       # Precio de venta
    cost_price = db.Column(db.Numeric(12, 2), default=0)                   # Precio de costo

    stock = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=5)

    image_url = db.Column(db.String(500))
    active = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)  # Para pantalla clientes

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    sale_items = db.relationship('SaleItem', backref='product', lazy='dynamic')

    @property
    def profit_margin(self):
        try:
            if self.cost_price and float(self.cost_price) > 0:
                return round(((float(self.price) - float(self.cost_price)) / float(self.price)) * 100, 1)
        except Exception:
            pass
        return 0

    @property
    def low_stock(self):
        return self.stock <= self.min_stock

    @property
    def image_src(self):
        if self.image_url:
            if self.image_url.startswith('http'):
                return self.image_url
            from flask import url_for
            return url_for('static', filename=f'uploads/{self.image_url}')
        return None

    def __repr__(self):
        return f'<Product {self.sku} – {self.name}>'
