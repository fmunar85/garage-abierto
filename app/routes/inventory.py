from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.product import Product, Category, BarcodeSequence, ProductUnit
from app.models.supplier import Supplier
from app.models.stock_movement import StockMovement
from app.utils import admin_required
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import os
import uuid

inventory_bp = Blueprint('inventory', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _cloudinary_configured():
    """Devuelve True si las variables de entorno de Cloudinary están seteadas."""
    return all(os.environ.get(k) for k in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET'))


def save_uploaded_image(file):
    """Sube la imagen a Cloudinary (producción) o al filesystem local (desarrollo).
    Devuelve la URL pública (Cloudinary) o el nombre de archivo (local).
    """
    if not file or not allowed_file(file.filename):
        return None

    # ── Cloudinary (Railway / producción) ─────────────────────────────────────
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    api_key    = os.environ.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')

    if cloud_name and api_key and api_secret:
        try:
            import cloudinary
            import cloudinary.uploader
            cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)
            result = cloudinary.uploader.upload(
                file,
                folder='garage_abierto/productos',
                transformation=[{'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'auto'}],
            )
            return result['secure_url']   # URL absoluta HTTPS → se persiste en BD
        except Exception as e:
            current_app.logger.error(f'Cloudinary upload failed: {e}')
            # fallback a local

    # ── Filesystem local (desarrollo) ─────────────────────────────────────────
    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    return filename   # nombre relativo → image_src lo convierte a URL


@inventory_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    category_id = request.args.get('cat', type=int)
    stock_filter = request.args.get('stock', '')
    active_filter = request.args.get('activo', '1')

    query = Product.query
    if active_filter == '0':
        query = query.filter_by(active=False)
    else:
        query = query.filter_by(active=True)

    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%'),
                Product.brand.ilike(f'%{search}%'),
            )
        )
    if category_id:
        query = query.filter_by(category_id=category_id)
    if stock_filter == 'low':
        query = query.filter(Product.stock <= Product.min_stock)
    elif stock_filter == 'out':
        query = query.filter(Product.stock == 0)

    products = query.order_by(Product.category_id, Product.name).paginate(page=page, per_page=24, error_out=False)
    categories = Category.query.order_by(Category.name).all()

    return render_template('inventory/index.html',
                           products=products,
                           categories=categories,
                           search=search,
                           category_id=category_id,
                           stock_filter=stock_filter,
                           active_filter=active_filter)


@inventory_bp.route('/producto/<int:pid>')
@login_required
def product_detail(pid):
    product = Product.query.get_or_404(pid)
    recent_items = product.sale_items.order_by(db.text('id desc')).limit(10).all()
    return render_template('inventory/detail.html', product=product, recent_items=recent_items)


@inventory_bp.route('/producto/nuevo', methods=['GET', 'POST'])
@login_required
def new_product():
    categories = Category.query.order_by(Category.name).all()
    suppliers = Supplier.query.filter_by(active=True).order_by(Supplier.name).all()
    cloudinary_ok = _cloudinary_configured()
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip().upper()
        if not sku or not request.form.get('name') or not request.form.get('price'):
            flash('SKU, nombre y precio son obligatorios.', 'danger')
            return render_template('inventory/form.html', product=None, categories=categories, suppliers=suppliers, cloudinary_ok=cloudinary_ok)
        if Product.query.filter_by(sku=sku).first():
            flash(f'El SKU {sku} ya existe.', 'danger')
            return render_template('inventory/form.html', product=None, categories=categories, suppliers=suppliers, cloudinary_ok=cloudinary_ok)

        image_filename = None
        file = request.files.get('image_file')
        image_filename = save_uploaded_image(file)
        if not image_filename:
            image_filename = request.form.get('image_url') or None

        p = Product(
            sku=sku,
            name=request.form.get('name', '').strip(),
            description=request.form.get('description', '').strip(),
            brand=request.form.get('brand', '').strip(),
            category_id=request.form.get('category_id') or None,
            supplier_id=request.form.get('supplier_id') or None,
            price=float(request.form.get('price', 0)),
            cost_price=float(request.form.get('cost_price', 0)),
            stock=int(request.form.get('stock', 0)),
            min_stock=int(request.form.get('min_stock', 5)),
            image_url=image_filename,
            featured='featured' in request.form,
        )
        db.session.add(p)
        db.session.commit()
        flash(f'Producto "{p.name}" creado correctamente.', 'success')
        return redirect(url_for('inventory.product_detail', pid=p.id))
    return render_template('inventory/form.html', product=None, categories=categories, suppliers=suppliers, cloudinary_ok=cloudinary_ok)


@inventory_bp.route('/producto/<int:pid>/editar', methods=['GET', 'POST'])
@login_required
def edit_product(pid):
    product = Product.query.get_or_404(pid)
    categories = Category.query.order_by(Category.name).all()
    suppliers = Supplier.query.filter_by(active=True).order_by(Supplier.name).all()
    cloudinary_ok = _cloudinary_configured()
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip().upper()
        existing = Product.query.filter_by(sku=sku).first()
        if existing and existing.id != pid:
            flash(f'El SKU {sku} ya pertenece a otro producto.', 'danger')
            return render_template('inventory/form.html', product=product, categories=categories, suppliers=suppliers, cloudinary_ok=cloudinary_ok)

        file = request.files.get('image_file')
        new_img = save_uploaded_image(file)
        if new_img:
            product.image_url = new_img
        elif request.form.get('image_url'):
            product.image_url = request.form.get('image_url')

        product.sku = sku
        product.name = request.form.get('name', '').strip()
        product.description = request.form.get('description', '').strip()
        product.brand = request.form.get('brand', '').strip()
        product.category_id = request.form.get('category_id') or None
        product.supplier_id = request.form.get('supplier_id') or None
        product.price = float(request.form.get('price', 0))
        product.cost_price = float(request.form.get('cost_price', 0))
        product.min_stock = int(request.form.get('min_stock', 5))
        product.active = 'active' in request.form
        product.featured = 'featured' in request.form
        db.session.commit()
        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('inventory.product_detail', pid=product.id))
    return render_template('inventory/form.html', product=product, categories=categories, suppliers=suppliers, cloudinary_ok=cloudinary_ok)


@inventory_bp.route('/producto/<int:pid>/stock', methods=['POST'])
@login_required
def adjust_stock(pid):
    product = Product.query.get_or_404(pid)
    amount    = int(request.form.get('amount', 0))
    operation = request.form.get('operation', 'add')
    mov_type  = request.form.get('mov_type', 'adjustment')
    reason    = request.form.get('reason', '').strip() or None

    qty_before = product.stock

    if operation == 'add':
        product.stock += amount
        flash(f'Se agregaron {amount} unidades. Stock actual: {product.stock}', 'success')
    elif operation == 'subtract':
        if product.stock < amount:
            flash('No hay suficiente stock para esa cantidad.', 'danger')
            return redirect(url_for('inventory.product_detail', pid=pid))
        product.stock -= amount
        flash(f'Se retiraron {amount} unidades. Stock actual: {product.stock}', 'success')
    elif operation == 'set':
        product.stock = amount
        flash(f'Stock ajustado a {amount} unidades.', 'success')

    qty_change = product.stock - qty_before
    mov = StockMovement(
        product_id=pid,
        user_id=current_user.id,
        type=mov_type,
        qty_before=qty_before,
        qty_change=qty_change,
        qty_after=product.stock,
        reason=reason,
    )
    db.session.add(mov)
    db.session.commit()
    return redirect(url_for('inventory.product_detail', pid=pid))


@inventory_bp.route('/recuento')
@login_required
@admin_required
def stock_count():
    """Página de conteo físico de inventario."""
    cat_id = request.args.get('cat', type=int)
    query = Product.query.filter_by(active=True)
    if cat_id:
        query = query.filter_by(category_id=cat_id)
    products = query.order_by(Product.category_id, Product.name).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('inventory/stock_count.html',
                           products=products,
                           categories=categories,
                           selected_cat=cat_id,
                           now=datetime.now(timezone.utc))


@inventory_bp.route('/recuento/aplicar', methods=['POST'])
@login_required
@admin_required
def apply_stock_count():
    """Aplica los ajustes del conteo físico."""
    data = request.form
    ajustados = 0
    sin_cambio = 0
    razon_global = data.get('reason_global', 'Conteo físico de inventario').strip()

    for key, val in data.items():
        if key.startswith('count_'):
            pid = int(key.split('_')[1])
            try:
                new_qty = int(val)
            except (ValueError, TypeError):
                continue
            product = Product.query.get(pid)
            if product is None:
                continue
            if product.stock == new_qty:
                sin_cambio += 1
                continue
            qty_before = product.stock
            product.stock = new_qty
            mov = StockMovement(
                product_id=pid,
                user_id=current_user.id,
                type='count',
                qty_before=qty_before,
                qty_change=new_qty - qty_before,
                qty_after=new_qty,
                reason=razon_global,
            )
            db.session.add(mov)
            ajustados += 1

    db.session.commit()
    flash(f'✅ Conteo aplicado: {ajustados} producto{"s" if ajustados != 1 else ""} ajustado{"s" if ajustados != 1 else ""}. {sin_cambio} sin cambios.', 'success')
    return redirect(url_for('inventory.stock_count'))


@inventory_bp.route('/movimientos')
@login_required
def movements():
    """Historial global de movimientos de stock."""
    page   = request.args.get('page', 1, type=int)
    pid    = request.args.get('product', type=int)
    mtype  = request.args.get('type', '')
    q      = StockMovement.query.join(Product)
    if pid:
        q = q.filter(StockMovement.product_id == pid)
    if mtype:
        q = q.filter(StockMovement.type == mtype)
    movements = q.order_by(StockMovement.created_at.desc()).paginate(page=page, per_page=30, error_out=False)
    products  = Product.query.order_by(Product.name).all()
    return render_template('inventory/movements.html',
                           movements=movements,
                           products=products,
                           selected_pid=pid,
                           selected_type=mtype)


@inventory_bp.route('/producto/<int:pid>/etiqueta')
@login_required
def product_label(pid):
    """Página de etiqueta con código de barras + QR para imprimir."""
    product = Product.query.get_or_404(pid)
    return render_template('inventory/label.html', product=product)



@inventory_bp.route('/codigos-barras')
@login_required
def barcodes():
    """Página de gestión de unidades físicas con código de barras."""
    products   = Product.query.filter_by(active=True).order_by(Product.name).all()
    categories = Category.query.order_by(Category.name).all()
    suppliers  = Supplier.query.filter_by(active=True).order_by(Supplier.name).all()

    # Conteos de unidades por producto
    from sqlalchemy import func
    unit_counts = dict(
        db.session.query(ProductUnit.product_id, func.count(ProductUnit.id))
        .group_by(ProductUnit.product_id)
        .all()
    )
    # Última recepción por producto
    last_reception = dict(
        db.session.query(ProductUnit.product_id, func.max(ProductUnit.received_at))
        .group_by(ProductUnit.product_id)
        .all()
    )

    total_products = len(products)
    total_units    = sum(unit_counts.values()) if unit_counts else 0
    sin_unidades   = sum(1 for p in products if unit_counts.get(p.id, 0) == 0)

    return render_template('inventory/barcodes.html',
                           products=products,
                           categories=categories,
                           suppliers=suppliers,
                           unit_counts=unit_counts,
                           last_reception=last_reception,
                           total_products=total_products,
                           total_units=total_units,
                           sin_unidades=sin_unidades)


@inventory_bp.route('/recibir-unidades', methods=['POST'])
@login_required
@admin_required
def receive_units():
    """Genera N ProductUnit para un producto. Devuelve JSON con los barcodes generados."""
    try:
        data       = request.get_json() or {}
        pid        = data.get('product_id')
        qty        = int(data.get('quantity', 0))

        if not pid or qty <= 0:
            return jsonify({'error': 'Producto y cantidad requeridos'}), 400
        if qty > 500:
            return jsonify({'error': 'Máximo 500 unidades por operación'}), 400

        product = Product.query.get_or_404(pid)
        units   = ProductUnit.generate_for_product(product, qty, user_id=current_user.id)
        db.session.commit()

        return jsonify({
            'ok':       True,
            'product':  product.name,
            'sku':      product.sku,
            'quantity': qty,
            'barcodes': [u.barcode for u in units],
            'ids':      [u.id for u in units],
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        current_app.logger.error(f'Error en receive_units: {traceback.format_exc()}')
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/unidad/<int:uid>', methods=['DELETE'])
@login_required
@admin_required
def delete_unit(uid):
    """Elimina una unidad física (ProductUnit)."""
    try:
        unit = ProductUnit.query.get_or_404(uid)
        db.session.delete(unit)
        db.session.commit()
        return jsonify({'ok': True, 'deleted_id': uid})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/api/producto/<int:pid>/unidades')
@login_required
def api_product_units(pid):
    """Devuelve JSON con todas las unidades de un producto."""
    product = Product.query.get_or_404(pid)
    units   = ProductUnit.query.filter_by(product_id=pid)\
                               .order_by(ProductUnit.received_at.desc())\
                               .all()
    return jsonify({
        'product': {'id': product.id, 'name': product.name, 'sku': product.sku},
        'units': [
            {
                'id':          u.id,
                'barcode':     u.barcode,
                'status':      u.status,
                'received_at': u.received_at.strftime('%d/%m/%Y %H:%M') if u.received_at else '—',
            }
            for u in units
        ],
    })


# ── API: buscar producto por SKU o código interno (para recepción con escáner) ─
@inventory_bp.route('/api/buscar-sku')
@login_required
def api_search_sku():
    raw = request.args.get('sku', '').strip().upper()
    if not raw:
        return jsonify({'error': 'SKU vacío'}), 400

    # Buscar por barcode de unidad (16 dígitos numéricos)
    p = None
    if raw.isdigit() and len(raw) == 16:
        unit = ProductUnit.query.filter_by(barcode=raw).first()
        if unit:
            p = unit.product

    # Por SKU exacto
    if not p:
        p = Product.query.filter(Product.sku.ilike(raw)).first()

    # Por SKU parcial
    if not p:
        p = Product.query.filter(Product.sku.ilike(f'%{raw}%')).first()

    if not p:
        return jsonify({'error': f'No se encontró ningún producto con código "{raw}"'}), 404

    return jsonify({
        'id':       p.id,
        'sku':      p.sku,
        'name':     p.name,
        'brand':    p.brand or '',
        'category': p.category_obj.name if p.category_obj else '',
        'price':    float(p.price),
        'cost':     float(p.cost_price) if p.cost_price else 0,
        'stock':    p.stock,
        'image':    p.image_src or '',
        'units':    ProductUnit.query.filter_by(product_id=p.id, status='disponible').count(),
    })


# ── Recepción de Mercadería ───────────────────────────────────────────────────
@inventory_bp.route('/recepcion')
@login_required
def reception():
    """Pantalla para ingresar mercadería escaneando o buscando por SKU."""
    suppliers = Supplier.query.filter_by(active=True).order_by(Supplier.name).all()
    return render_template('inventory/reception.html', suppliers=suppliers)


@inventory_bp.route('/recepcion/aplicar', methods=['POST'])
@login_required
def apply_reception():
    """Aplica el ingreso de mercadería: suma stock y registra movimientos."""
    data        = request.get_json()
    items       = data.get('items', [])
    note        = data.get('note', '').strip() or 'Recepción de mercadería'
    supplier_id = data.get('supplier_id') or None

    if not items:
        return jsonify({'error': 'Sin ítems'}), 400

    resultados = []
    for item in items:
        pid       = item.get('id')
        qty       = int(item.get('qty', 0))
        new_cost  = item.get('cost')   # puede ser None si no se actualizó

        if qty <= 0:
            continue

        p = Product.query.get(pid)
        if not p:
            continue

        qty_before = p.stock
        p.stock   += qty

        if new_cost is not None and float(new_cost) > 0:
            p.cost_price = float(new_cost)

        reason = note
        if supplier_id:
            sup = Supplier.query.get(supplier_id)
            if sup:
                reason = f'{note} — {sup.name}'

        mov = StockMovement(
            product_id=pid,
            user_id=current_user.id,
            type='reception',
            qty_before=qty_before,
            qty_change=qty,
            qty_after=p.stock,
            reason=reason,
        )
        db.session.add(mov)
        resultados.append({'sku': p.sku, 'name': p.name, 'qty': qty, 'stock_after': p.stock})

    db.session.commit()
    return jsonify({'ok': True, 'updated': len(resultados), 'items': resultados})


@inventory_bp.route('/producto/<int:pid>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_product(pid):
    product = Product.query.get_or_404(pid)
    product.active = False
    db.session.commit()
    flash(f'Producto "{product.name}" dado de baja.', 'warning')
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/categorias')
@login_required
@admin_required
def categories():
    cats = Category.query.order_by(Category.name).all()
    return render_template('inventory/categories.html', categories=cats)


@inventory_bp.route('/categorias/nueva', methods=['POST'])
@login_required
@admin_required
def new_category():
    name = request.form.get('name', '').strip()
    icon = request.form.get('icon', 'bi-box').strip()
    color = request.form.get('color', '#2196F3').strip()
    if name and not Category.query.filter_by(name=name).first():
        cat = Category(name=name, icon=icon, color=color)
        db.session.add(cat)
        db.session.commit()
        flash(f'Categoría "{name}" creada.', 'success')
    else:
        flash('Nombre inválido o ya existe esa categoría.', 'danger')
    return redirect(url_for('inventory.categories'))
