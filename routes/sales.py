from flask import Blueprint, request, jsonify
from models.database_models import Sale, SaleItem
from services.inventory_service import create_sale

bp=Blueprint("sales",__name__,url_prefix="/api")
@bp.post("/sales")
def add_sale():
    try:
        sale=create_sale(request.get_json(force=True).get("items"));return jsonify({"ok":True,"invoice_number":sale.invoice_number,"total":float(sale.total_amount),"items":[{"product":i.product.name,"quantity":i.quantity,"line_total":float(i.line_total)} for i in sale.items]}),201
    except (ValueError,KeyError,TypeError) as e:return jsonify({"ok":False,"error":str(e)}),400
@bp.get("/sales")
def sales():
    rows=Sale.query.order_by(Sale.sold_at.desc()).limit(100).all()
    return jsonify({"ok":True,"items":[{"id":s.id,"invoice_number":s.invoice_number,"sold_at":s.sold_at.isoformat(),"total":float(s.total_amount)} for s in rows]})
