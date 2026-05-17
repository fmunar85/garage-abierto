from app import db
from datetime import datetime, timezone


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(100))
    salary = db.Column(db.Numeric(12, 2), default=0)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    dni = db.Column(db.String(20))
    address = db.Column(db.Text)
    hire_date = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Employee {self.name}>'
