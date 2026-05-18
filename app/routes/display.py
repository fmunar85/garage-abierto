from flask import Blueprint, render_template
from app.models.product import Product, Category
from app.models.promotion import BankPromotion
from datetime import date

display_bp = Blueprint('display', __name__)


@display_bp.route('/')
def index():
    categories = Category.query.order_by(Category.name).all()
    products = Product.query.filter_by(active=True).order_by(Product.category_id, Product.name).all()
    featured = Product.query.filter_by(active=True, featured=True).all()
    today = date.today()
    promos = BankPromotion.query.filter(
        BankPromotion.active == True,
        BankPromotion.valid_from <= today,
        BankPromotion.valid_until >= today
    ).all()
    return render_template('display/index.html', categories=categories, products=products,
                           featured=featured, promos=promos)
