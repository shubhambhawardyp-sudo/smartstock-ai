from datetime import date, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from models.database_models import db, Product, Sale, SaleItem, DailyProductSale, Category
from services.forecasting_service import risk_and_reorder

bp=Blueprint("analytics",__name__,url_prefix="/api")
@bp.get("/dashboard")
def dashboard():
    start=date.today()-timedelta(days=request.args.get("days",30,type=int)-1)
    revenue=db.session.query(func.coalesce(func.sum(Sale.total_amount),0)).filter(func.date(Sale.sold_at)>=start).scalar()
    products=Product.query.all(); total_stock=sum(p.stock_quantity for p in products); value=sum(float(p.cost_price)*p.stock_quantity for p in products)
    recent=DailyProductSale.query.filter(DailyProductSale.sale_date>=start).all()
    by_day={}
    for r in recent: by_day[r.sale_date.isoformat()]=by_day.get(r.sale_date.isoformat(),0)+float(r.revenue)
    category_value=db.session.query(Category.name,func.coalesce(func.sum(Product.cost_price*Product.stock_quantity),0)).join(Product).group_by(Category.name).all()
    top=db.session.query(Product.name,func.coalesce(func.sum(SaleItem.quantity),0)).join(SaleItem).join(Sale).filter(func.date(Sale.sold_at)>=start).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(5).all()
    avg_forecast={p.id:db.session.query(func.avg(__import__('models.database_models',fromlist=['DemandPrediction']).DemandPrediction.predicted_units)).filter_by(product_id=p.id).scalar() for p in products}
    alerts=[]
    for p in products:
        f=float(avg_forecast.get(p.id) or 0); calc=risk_and_reorder(p,f)
        if p.stock_quantity<=p.reorder_threshold or calc["risk"]!="low":alerts.append({"product":p.name,"sku":p.sku,"stock":p.stock_quantity,"forecast_daily":round(f,2),**calc})
    return jsonify({"ok":True,"cards":{"product_count":len(products),"units_in_stock":total_stock,"inventory_value":round(value,2),"revenue":round(float(revenue),2),"low_stock_count":sum(p.stock_quantity<=p.reorder_threshold for p in products),"stockout_risk_count":sum(a["risk"]=="high" for a in alerts),"next_7_day_demand":round(sum((avg_forecast[p.id] or 0)*7 for p in products),2)},"charts":{"daily_revenue":{"labels":list(by_day),"values":list(by_day.values())},"category_inventory":{"labels":[x[0] for x in category_value],"values":[float(x[1]) for x in category_value]},"top_products":{"labels":[x[0] for x in top],"values":[int(x[1]) for x in top]}},"alerts":alerts[:12]})
