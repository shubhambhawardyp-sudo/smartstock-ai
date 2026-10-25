from sqlalchemy.dialects.mysql import insert
from models.database_models import db, DailyProductSale

def load_daily(aggregates):
    count=0
    for row in aggregates.to_dict("records"):
        stmt=insert(DailyProductSale).values(product_id=int(row["product_id"]),sale_date=row["sale_date"],units_sold=int(row["units_sold"]),revenue=row["revenue"])
        stmt=stmt.on_duplicate_key_update(units_sold=stmt.inserted.units_sold,revenue=stmt.inserted.revenue)
        db.session.execute(stmt);count+=1
    db.session.commit();return count
