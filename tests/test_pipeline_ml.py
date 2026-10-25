import pandas as pd
from pipelines.transform import transform_sales
from models.demand_model import make_features
from services.forecasting_service import risk_and_reorder
from models.database_models import Product

def test_transform_aggregates_and_drops_invalid():
    f=pd.DataFrame([{"sale_id":1,"sold_at":"2026-10-01","product_id":2,"quantity":2,"line_total":6},{"sale_id":2,"sold_at":"2026-10-01","product_id":2,"quantity":1,"line_total":3},{"sale_id":3,"sold_at":"bad","product_id":2,"quantity":4,"line_total":12}])
    out=transform_sales(f);assert len(out)==1;assert out.iloc[0].units_sold==3

def test_features_use_prior_observations_only():
    f=pd.DataFrame({"product_id":[1]*10,"sale_date":pd.date_range('2026-01-01',periods=10),"units_sold":range(10)})
    out=make_features(f);assert out.iloc[0].lag_1==6;assert out.iloc[0].lag_7==0

def test_reorder_math_is_explainable():
    p=Product(stock_quantity=5,reorder_threshold=4,lead_time_days=3);r=risk_and_reorder(p,2)
    assert r['reorder_point']==10;assert r['suggested_quantity']==19;assert r['risk']=='high';assert 'lead-time demand' in r['explanation']
