import pandas as pd
from sqlalchemy import text
from models.database_models import db

def extract_sales():
    return pd.read_sql(text("SELECT s.id sale_id,s.sold_at,si.product_id,si.quantity,si.line_total FROM sales s JOIN sale_items si ON si.sale_id=s.id"),db.engine)
def extract_products(): return pd.read_sql(text("SELECT id product_id,sku,name,category_id FROM products"),db.engine)
def extract_movements(): return pd.read_sql(text("SELECT id,product_id,movement_type,quantity,reason,created_at FROM stock_movements"),db.engine)
