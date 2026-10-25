"""Explicitly labeled synthetic demonstration history; never use as real accuracy evidence."""
import argparse, math, random
from datetime import date,timedelta
from app import create_app
from models.database_models import db,Product,DailyProductSale

def run(days):
    app=create_app()
    with app.app_context():
        products=Product.query.all()
        if not products:raise SystemExit("Create products before generating demo data")
        random.seed(17);today=date.today();count=0
        for p in products:
            for n in range(days,0,-1):
                d=today-timedelta(days=n);demand=max(0,round(3+2*math.sin((d.weekday()+p.id)/2)+random.gauss(0,1.1)))
                row=db.session.query(DailyProductSale).filter_by(product_id=p.id,sale_date=d).one_or_none()
                if row is None:db.session.add(DailyProductSale(product_id=p.id,sale_date=d,units_sold=demand,revenue=demand*p.selling_price));count+=1
        db.session.commit();print(f"Added {count} synthetic product-day rows (demo data; not real observations).")

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--days",type=int,default=120);run(parser.parse_args().days)
