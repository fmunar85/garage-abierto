from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()


def _run_column_migrations(db):
    """Aplica ALTER TABLE para columnas nuevas que no existen todavía en la BD."""
    migrations = [
        # (tabla, columna, definición SQL)
        ('products',          'internal_barcode', 'VARCHAR(16)'),
        ('barcode_sequences', 'last_seq',         None),           # tabla nueva → solo create_all
        ('stock_movements',   'product_id',       None),           # tabla nueva → solo create_all
    ]
    with db.engine.connect() as conn:
        for table, column, col_def in migrations:
            if col_def is None:
                continue  # tablas nuevas se crean con create_all, no necesitan ALTER
            try:
                result = conn.execute(
                    db.text(
                        "SELECT 1 FROM information_schema.columns "
                        "WHERE table_name = :t AND column_name = :c"
                    ),
                    {'t': table, 'c': column},
                )
                if result.fetchone() is None:
                    conn.execute(db.text(
                        f'ALTER TABLE {table} ADD COLUMN {column} {col_def}'
                    ))
                    conn.commit()
            except Exception as e:
                # Si la tabla no existe aún, create_all la creará después
                conn.rollback()
                import logging
                logging.getLogger(__name__).warning(
                    'Migration skipped for %s.%s: %s', table, column, e
                )


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'garage-abierto-secret-2024')
    db_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/garage_abierto')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor iniciá sesión para continuar.'
    login_manager.login_message_category = 'warning'

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.inventory import inventory_bp
    from app.routes.sales_bp import sales_bp
    from app.routes.display import display_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.customers import customers_bp
    from app.routes.employees import employees_bp
    from app.routes.promotions import promotions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(inventory_bp, url_prefix='/inventario')
    app.register_blueprint(sales_bp, url_prefix='/ventas')
    app.register_blueprint(display_bp, url_prefix='/display')
    app.register_blueprint(suppliers_bp, url_prefix='/proveedores')
    app.register_blueprint(customers_bp, url_prefix='/clientes')
    app.register_blueprint(employees_bp, url_prefix='/empleados')
    app.register_blueprint(promotions_bp, url_prefix='/promociones')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Auto-create any new tables (safe: does not drop existing ones)
    with app.app_context():
        from app.models import User, Product, Category, Supplier, Customer, Employee, Sale, SaleItem, BankPromotion  # noqa
        db.create_all()

        # ── Migraciones de columnas nuevas (ALTER TABLE si no existen) ──────
        _run_column_migrations(db)

    # Custom Jinja2 filters
    @app.template_filter('currency')
    def currency_filter(value):
        if value is None:
            return '$0'
        try:
            return '${:,.0f}'.format(float(value)).replace(',', '.')
        except (ValueError, TypeError):
            return '$0'

    @app.template_filter('pct')
    def pct_filter(value):
        try:
            return f'{float(value):.1f}%'
        except (ValueError, TypeError):
            return '0%'

    return app
