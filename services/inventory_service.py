from decimal import Decimal
import re
from sqlalchemy.exc import IntegrityError
from models.database_models import db, Product, StockMovement, Sale, SaleItem


def normalized_sku(sku):
    """Canonicalize SKU formatting so separators/case cannot create duplicates."""
    return re.sub(r"[^A-Z0-9]", "", str(sku).upper())


def find_sku_duplicate(sku, exclude_id=None):
    key = normalized_sku(sku)
    for product_id, stored_sku, name in Product.query.with_entities(Product.id, Product.sku, Product.name).all():
        if product_id != exclude_id and normalized_sku(stored_sku) == key:
            return stored_sku, name
    return None


def validate_product(payload, existing=None):
    required = ("sku", "name", "category_id")
    if any(not payload.get(k) for k in required):
        raise ValueError("SKU, product name, and category are required")
    try:
        cost = Decimal(str(payload.get("cost_price", 0)))
        price = Decimal(str(payload.get("selling_price", 0)))
        stock = int(payload.get("stock_quantity", existing.stock_quantity if existing else 0))
        threshold = int(payload.get("reorder_threshold", 5))
        lead = int(payload.get("lead_time_days", 7))
        category = int(payload["category_id"])
    except (ValueError, TypeError, ArithmeticError):
        raise ValueError("Prices and quantities must be valid numbers")
    if min(cost, price) < 0 or min(stock, threshold, lead) < 0:
        raise ValueError("Prices and quantities cannot be negative")
    return {"sku": str(payload["sku"]).strip().upper(), "name": str(payload["name"]).strip(), "description": payload.get("description", ""), "category_id": category, "supplier_id": payload.get("supplier_id") or None, "cost_price": cost, "selling_price": price, "stock_quantity": stock, "reorder_threshold": threshold, "lead_time_days": lead}


def create_sale(items):
    """Create invoice and stock movements atomically; raises ValueError on bad stock."""
    if not isinstance(items, list) or not items:
        raise ValueError("At least one sale item is required")
    try:
        sale = Sale(invoice_number="PENDING")
        db.session.add(sale)
        db.session.flush()
        sale.invoice_number = f"SS-{sale.id:06d}"
        total = Decimal("0.00")
        for item in items:
            product = db.session.get(Product, int(item["product_id"]))
            qty = int(item["quantity"])
            if product is None or qty <= 0:
                raise ValueError("Each sale needs a valid product and positive quantity")
            if product.stock_quantity < qty:
                raise ValueError(f"Insufficient stock for {product.name}; available {product.stock_quantity}")
            line = Decimal(product.selling_price) * qty
            product.stock_quantity -= qty
            total += line
            db.session.add(SaleItem(sale=sale, product=product, quantity=qty, unit_price=product.selling_price, line_total=line))
            db.session.add(StockMovement(product=product, movement_type="SALE", quantity=-qty, reason="Completed sale", reference=sale.invoice_number))
        sale.total_amount = total
        db.session.commit()
        return sale
    except Exception:
        db.session.rollback()
        raise


def adjust_stock(product, quantity, reason):
    quantity = int(quantity)
    new_stock = product.stock_quantity + quantity
    if quantity == 0 or new_stock < 0 or not reason.strip():
        raise ValueError("Adjustment must be non-zero, leave stock non-negative, and include a reason")
    product.stock_quantity = new_stock
    db.session.add(StockMovement(product=product, movement_type="ADJUSTMENT", quantity=quantity, reason=reason.strip()))
    db.session.commit()
