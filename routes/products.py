from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from models.database_models import db, Product, Category, Supplier, StockMovement
from services.inventory_service import validate_product, adjust_stock, find_sku_duplicate

bp = Blueprint("products", __name__, url_prefix="/api")

def error(message, status=400): return jsonify({"ok": False, "error": message}), status

@bp.get("/products")
def list_products():
    q = Product.query
    term = request.args.get("q", "").strip()
    if term: q = q.filter(db.or_(Product.name.ilike(f"%{term}%"), Product.sku.ilike(f"%{term}%")))
    if request.args.get("category_id", type=int): q = q.filter_by(category_id=request.args.get("category_id", type=int))
    page = max(1, request.args.get("page", 1, type=int)); size = min(100, max(1, request.args.get("per_page", 12, type=int)))
    pagination = q.order_by(Product.name).paginate(page=page, per_page=size, error_out=False)
    return jsonify({"ok": True, "items": [serialize(p) for p in pagination.items], "page": page, "pages": pagination.pages, "total": pagination.total})

def serialize(p):
    return {"id":p.id,"sku":p.sku,"name":p.name,"description":p.description,"category_id":p.category_id,"category":p.category.name,"supplier_id":p.supplier_id,"supplier":p.supplier.name if p.supplier else None,"cost_price":float(p.cost_price),"selling_price":float(p.selling_price),"stock_quantity":p.stock_quantity,"reorder_threshold":p.reorder_threshold,"lead_time_days":p.lead_time_days,"updated_at":p.updated_at.isoformat()}

@bp.post("/products")
def create_product():
    try:
        data = validate_product(request.get_json(force=True))
        duplicate = find_sku_duplicate(data["sku"])
        if duplicate:
            return error(f"SKU matches existing product {duplicate[1]} ({duplicate[0]}). Use + Stock to add inventory instead.", 409)
        p=Product(**data); db.session.add(p); db.session.commit(); return jsonify({"ok":True,"item":serialize(p)}),201
    except ValueError as e: db.session.rollback(); return error(str(e))
    except IntegrityError: db.session.rollback(); return error("SKU already exists or category is invalid",409)

@bp.route("/products/<int:product_id>", methods=["GET","PUT","DELETE"])
def product_detail(product_id):
    p=db.session.get(Product,product_id)
    if not p: return error("Product not found",404)
    if request.method=="GET": return jsonify({"ok":True,"item":serialize(p)})
    if request.method=="DELETE": db.session.delete(p); db.session.commit(); return jsonify({"ok":True})
    try:
        data = validate_product(request.get_json(force=True),p)
        duplicate = find_sku_duplicate(data["sku"], exclude_id=p.id)
        if duplicate:
            return error(f"SKU matches existing product {duplicate[1]} ({duplicate[0]}).", 409)
        for k,v in data.items(): setattr(p,k,v)
        db.session.commit(); return jsonify({"ok":True,"item":serialize(p)})
    except ValueError as e: db.session.rollback(); return error(str(e))
    except IntegrityError: db.session.rollback(); return error("SKU already exists or category is invalid",409)

@bp.get("/categories")
def categories(): return jsonify({"ok":True,"items":[{"id":c.id,"name":c.name,"product_count":len(c.products)} for c in Category.query.order_by(Category.name)]})

@bp.post("/categories")
def create_category():
    data=request.get_json(force=True); name=str(data.get("name","")).strip()
    if not name:return error("Category name is required")
    c=Category(name=name,description=data.get("description"));db.session.add(c)
    try:db.session.commit();return jsonify({"ok":True,"id":c.id,"name":c.name}),201
    except IntegrityError:db.session.rollback();return error("Category already exists",409)

@bp.get("/suppliers")
def suppliers(): return jsonify({"ok":True,"items":[{"id":s.id,"name":s.name,"contact_name":s.contact_name,"email":s.email,"phone":s.phone} for s in Supplier.query.order_by(Supplier.name)]})

@bp.post("/suppliers")
def create_supplier():
    d=request.get_json(force=True);name=str(d.get("name","")).strip()
    if not name:return error("Supplier name is required")
    s=Supplier(name=name,contact_name=d.get("contact_name"),email=d.get("email"),phone=d.get("phone"));db.session.add(s);db.session.commit();return jsonify({"ok":True,"id":s.id}),201

@bp.post("/products/<int:product_id>/adjust")
def stock_adjust(product_id):
    p=db.session.get(Product,product_id)
    if not p:return error("Product not found",404)
    try:adjust_stock(p,request.get_json(force=True).get("quantity"),str(request.get_json().get("reason","")));return jsonify({"ok":True,"item":serialize(p)})
    except (ValueError,TypeError) as e:db.session.rollback();return error(str(e))

@bp.get("/movements")
def movements():
    rows=StockMovement.query.order_by(StockMovement.created_at.desc()).limit(200).all()
    return jsonify({"ok":True,"items":[{"id":r.id,"product":r.product.name,"sku":r.product.sku,"type":r.movement_type,"quantity":r.quantity,"reason":r.reason,"reference":r.reference,"created_at":r.created_at.isoformat()} for r in rows]})
