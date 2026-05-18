from app import db
from datetime import datetime, timezone


class BarcodeSequence(db.Model):
    """Tabla de un solo registro: contador global de códigos internos."""
    __tablename__ = 'barcode_sequence'

    id       = db.Column(db.Integer, primary_key=True)   # siempre será 1
    last_val = db.Column(db.Integer, default=0, nullable=False)

    @classmethod
    def next_val(cls):
        """Retorna el siguiente valor de secuencia e incrementa atómicamente."""
        row = cls.query.with_for_update().get(1)
        if row is None:
            row = cls(id=1, last_val=0)
            db.session.add(row)
        row.last_val += 1
        db.session.flush()   # flush para que el valor quede disponible antes del commit
        return row.last_val


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
    internal_barcode = db.Column(db.String(16), unique=True, nullable=True, index=True)
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

    def generate_internal_barcode(self):
        """
        Genera y asigna el código de barras interno de 16 dígitos:
          CAT(3) + SUP(3) + PROD(4) + SEQ(6)
        Persiste el valor en self.internal_barcode.
        Llama a db.session.flush() antes de devolver para que el SEQ quede reservado.
        """
        cat  = str(self.category_id  or 0).zfill(3)[-3:]
        sup  = str(self.supplier_id  or 0).zfill(3)[-3:]
        prod = str(self.id           or 0).zfill(4)[-4:]
        seq  = str(BarcodeSequence.next_val()).zfill(6)[-6:]
        self.internal_barcode = f'{cat}{sup}{prod}{seq}'
        return self.internal_barcode


class ProductUnit(db.Model):
    """Una unidad física de un producto, identificada por su código de barras único."""
    __tablename__ = 'product_units'

    id          = db.Column(db.Integer, primary_key=True)
    barcode     = db.Column(db.String(16), unique=True, nullable=False, index=True)
    product_id  = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    received_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    received_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status      = db.Column(db.String(20), default='disponible')  # disponible | vendida | dañada

    product = db.relationship('Product', backref=db.backref('units', lazy='dynamic'))

    def __repr__(self):
        return f'<ProductUnit {self.barcode}>'

    @classmethod
    def generate_for_product(cls, product, quantity, user_id=None):
        """
        Crea `quantity` instancias de ProductUnit con barcodes únicos consecutivos.
        Formato: CAT(3) + SUP(3) + PROD(4) + SEQ(6) = 16 dígitos
        Devuelve la lista de objetos creados (SIN hacer commit).
        """
        cat  = str(product.category_id or 0).zfill(3)[-3:]
        sup  = str(product.supplier_id  or 0).zfill(3)[-3:]
        prod = str(product.id           or 0).zfill(4)[-4:]
        units = []
        for _ in range(quantity):
            seq  = str(BarcodeSequence.next_val()).zfill(6)[-6:]
            unit = cls(
                barcode    = f'{cat}{sup}{prod}{seq}',
                product_id = product.id,
                received_by= user_id,
            )
            db.session.add(unit)
            units.append(unit)
        return units
