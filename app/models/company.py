from app import db


class CompanySettings(db.Model):
    __tablename__ = 'company_settings'

    id            = db.Column(db.Integer, primary_key=True)
    company_name  = db.Column(db.String(120), nullable=False, default='Mi Empresa')
    tagline       = db.Column(db.String(200), default='Artículos de Baño')
    logo_url      = db.Column(db.String(500), nullable=True)   # URL externa (Cloudinary, etc.)
    primary_color = db.Column(db.String(20), default='#1a5fb4')
    accent_color  = db.Column(db.String(20), default='#2ec4a9')
    address       = db.Column(db.String(250), nullable=True)
    phone         = db.Column(db.String(50), nullable=True)
    whatsapp      = db.Column(db.String(50), nullable=True)
    email         = db.Column(db.String(120), nullable=True)
    website       = db.Column(db.String(200), nullable=True)

    @classmethod
    def get(cls):
        """Devuelve la única fila de configuración; la crea si no existe."""
        settings = cls.query.first()
        if not settings:
            settings = cls(company_name='Garage Abierto', tagline='Artículos de Baño')
            db.session.add(settings)
            db.session.commit()
        return settings
