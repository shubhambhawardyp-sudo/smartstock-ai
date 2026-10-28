"""SQLAlchemy operational and analytical schema for SmartStock AI."""
from datetime import datetime, date
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, UniqueConstraint, Index

db = SQLAlchemy()


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    products = db.relationship("Product", back_populates="category")


class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact_name = db.Column(db.String(120))
    email = db.Column(db.String(254))
    phone = db.Column(db.String(40))
    products = db.relationship("Product", back_populates="supplier")


class Product(db.Model):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("cost_price >= 0"), CheckConstraint("selling_price >= 0"), CheckConstraint("stock_quantity >= 0"), CheckConstraint("reorder_threshold >= 0"), Index("ix_products_category", "category_id"))
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(160), nullable=False, index=True)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="SET NULL"))
    cost_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    selling_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_threshold = db.Column(db.Integer, nullable=False, default=5)
    lead_time_days = db.Column(db.Integer, nullable=False, default=7)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    category = db.relationship("Category", back_populates="products")
    supplier = db.relationship("Supplier", back_populates="products")


class Sale(db.Model):
    __tablename__ = "sales"
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(40), unique=True, nullable=False)
    sold_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(db.Model):
    __tablename__ = "sale_items"
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product")


class StockMovement(db.Model):
    __tablename__ = "stock_movements"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    movement_type = db.Column(db.Enum("IN", "OUT", "ADJUSTMENT", "SALE", name="movement_type"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    reference = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    product = db.relationship("Product")


class DailyProductSale(db.Model):
    __tablename__ = "daily_product_sales"
    __table_args__ = (UniqueConstraint("product_id", "sale_date", name="uq_daily_product_date"),)
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    sale_date = db.Column(db.Date, nullable=False)
    units_sold = db.Column(db.Integer, nullable=False, default=0)
    revenue = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    product = db.relationship("Product")


class DemandPrediction(db.Model):
    __tablename__ = "demand_predictions"
    __table_args__ = (UniqueConstraint("product_id", "forecast_date", "model_version", name="uq_prediction_product_date_version"),)
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    predicted_units = db.Column(db.Float, nullable=False)
    model_version = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    product = db.relationship("Product")


class PipelineLog(db.Model):
    __tablename__ = "pipeline_logs"
    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)
    records_processed = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text)


class ModelMetric(db.Model):
    __tablename__ = "model_metrics"
    id = db.Column(db.Integer, primary_key=True)
    model_version = db.Column(db.String(60), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    metric_name = db.Column(db.String(40), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    evaluated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "staff", name="user_role"), nullable=False, default="staff")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
