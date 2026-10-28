from datetime import date
from flask import Blueprint, request, jsonify
from models.database_models import Sale
from services.inventory_service import create_sale

bp=Blueprint("sales",__name__,url_prefix="/api")
@bp.post("/sales")
def add_sale():
    try:
        payload=request.get_json(force=True)
        sale_date=payload.get("sale_date") or date.today().isoformat()
        sale=create_sale(payload.get("items"),sale_date=sale_date)
        return jsonify({"ok":True,"invoice_number":sale.invoice_number,"sale_date":sale.sold_at.date().isoformat(),"total":float(sale.total_amount),"items":[{"product_id":i.product_id,"product":i.product.name,"quantity":i.quantity,"line_total":float(i.line_total)} for i in sale.items]}),201
    except (ValueError,KeyError,TypeError) as e:return jsonify({"ok":False,"error":str(e)}),400
@bp.get("/sales")
def sales():
    rows=Sale.query.order_by(Sale.sold_at.desc()).limit(100).all()
    return jsonify({"ok":True,"items":[{"id":s.id,"invoice_number":s.invoice_number,"sale_date":s.sold_at.date().isoformat(),"sold_at":s.sold_at.isoformat(),"total":float(s.total_amount),"items":[{"product_id":i.product_id,"product":i.product.name,"sku":i.product.sku,"quantity":i.quantity,"unit_price":float(i.unit_price),"line_total":float(i.line_total)} for i in s.items]} for s in rows]})
