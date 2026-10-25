import pandas as pd

def transform_sales(frame):
    required={"sale_id","sold_at","product_id","quantity","line_total"}
    if not required.issubset(frame.columns):raise ValueError(f"Missing columns: {sorted(required-set(frame.columns))}")
    data=frame.copy();data["sold_at"]=pd.to_datetime(data["sold_at"],errors="coerce");data["quantity"]=pd.to_numeric(data["quantity"],errors="coerce");data["line_total"]=pd.to_numeric(data["line_total"],errors="coerce")
    data=data.dropna(subset=["sale_id","sold_at","product_id","quantity","line_total"])
    data=data[(data.quantity>0)&(data.line_total>=0)]
    data["sale_date"]=data.sold_at.dt.date
    return data.groupby(["product_id","sale_date"],as_index=False).agg(units_sold=("quantity","sum"),revenue=("line_total","sum"))
