import os, pytest
from app import create_app
from models.database_models import db

@pytest.fixture
def app():
    uri=os.environ.get("TEST_DATABASE_URL")
    if not uri or "smartstock_test" not in uri:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated disposable MySQL schema containing 'smartstock_test'")
    app=create_app({"TESTING":True,"SQLALCHEMY_DATABASE_URI":uri,"WTF_CSRF_ENABLED":False})
    with app.app_context():db.create_all()
    yield app
    with app.app_context():db.session.remove();db.drop_all()

@pytest.fixture
def client(app):
    from werkzeug.security import generate_password_hash
    from models.database_models import User
    with app.app_context():
        user=User(username="test-user",password_hash=generate_password_hash("test-password-long-enough"),role="admin")
        db.session.add(user);db.session.commit()
    client=app.test_client()
    client.post("/login",data={"username":"test-user","password":"test-password-long-enough"})
    return client

@pytest.fixture
def sample_ids(app):
    from models.database_models import Category,Supplier,Product
    with app.app_context():
        c=Category(name="Test pantry");s=Supplier(name="Test supplier");db.session.add_all([c,s]);db.session.flush();p=Product(sku="TST-1",name="Test item",category_id=c.id,supplier_id=s.id,cost_price=2,selling_price=4,stock_quantity=10,reorder_threshold=3,lead_time_days=4);db.session.add(p);db.session.commit();return {"category_id":c.id,"supplier_id":s.id,"product_id":p.id}
