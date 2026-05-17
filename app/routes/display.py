from flask import Blueprint, render_template
from app.models.product import Product, Category

display_bp = Blueprint('display', __name__)


@display_bp.route('/')
def index():
    categories = Category.query.order_by(Category.name).all()
    products = Product.query.filter_by(active=True).order_by(Product.category_id, Product.name).all()
    featured = Product.query.filter_by(active=True, featured=True).all()
    return render_template('display/index.html', categories=categories, products=products, featured=featured)
