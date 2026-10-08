from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Batch(db.Model):
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(100), unique=True, nullable=False)
    product_type = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='batch', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    status = db.Column(db.String(50), default='REGISTERED', index=True)
    current_station = db.Column(db.String(100), default='Registration', index=True)
    result = db.Column(db.String(50), default='Pending', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    events = db.relationship('ProductionEvent', backref='product', lazy=True)
    test_results = db.relationship('TestResult', backref='product', lazy=True)
    defects = db.relationship('Defect', backref='product', lazy=True)

class Station(db.Model):
    __tablename__ = 'stations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    events = db.relationship('ProductionEvent', backref='station', lazy=True)

class ProductionEvent(db.Model):
    __tablename__ = 'production_events'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('stations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50))
    notes = db.Column(db.Text)

class TestResult(db.Model):
    __tablename__ = 'test_results'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    parameter = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    passed = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Defect(db.Model):
    __tablename__ = 'defects'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    station_id = db.Column(db.Integer, db.ForeignKey('stations.id'), nullable=True)
    parameter = db.Column(db.String(100), nullable=True)
    actual_value = db.Column(db.String(100), nullable=True)
    expected_value = db.Column(db.String(100), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(50))
    status = db.Column(db.String(50), default='Open')
    resolved = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class TestLimit(db.Model):
    __tablename__ = 'test_limits'
    id = db.Column(db.Integer, primary_key=True)
    parameter = db.Column(db.String(100), unique=True, nullable=False)
    min_value = db.Column(db.Float, nullable=True)
    max_value = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(50), nullable=True)
