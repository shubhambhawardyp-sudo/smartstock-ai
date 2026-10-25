from models.database_models import db,Product

def product_payload(category_id,**kw):return {"sku":"NEW-1","name":"New item","category_id":category_id,"cost_price":1,"selling_price":2,"stock_quantity":7,"reorder_threshold":2,"lead_time_days":3,**kw}

def test_product_create_and_duplicate_sku(client,sample_ids):
    data=product_payload(sample_ids["category_id"]);r=client.post('/api/products',json=data);assert r.status_code==201
    duplicate=client.post('/api/products',json=data);assert duplicate.status_code==409

def test_product_update(client,sample_ids):
    r=client.put(f"/api/products/{sample_ids['product_id']}",json=product_payload(sample_ids['category_id'],sku="TST-1",name="Changed"));assert r.status_code==200;assert r.json['item']['name']=="Changed"

def test_sale_reduces_stock_and_insufficient_rolls_back(client,sample_ids,app):
    pid=sample_ids['product_id'];r=client.post('/api/sales',json={"items":[{"product_id":pid,"quantity":3}]});assert r.status_code==201
    with app.app_context():assert db.session.get(Product,pid).stock_quantity==7
    fail=client.post('/api/sales',json={"items":[{"product_id":pid,"quantity":99}]});assert fail.status_code==400
    with app.app_context():assert db.session.get(Product,pid).stock_quantity==7
