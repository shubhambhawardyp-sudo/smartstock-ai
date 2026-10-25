"""Import daily sales aggregates from CSV into MySQL.

Run from the project folder:
    python -m pipelines.import_daily_csv

CSV columns: sku, sale_date, units_sold, revenue. Existing identical rows are
safe to import again; conflicting product/date rows are rejected to protect
existing data.
"""
import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from app import create_app
from models.database_models import db, Product, DailyProductSale

DEFAULT_CSV = Path(__file__).resolve().parents[1] / "data" / "sample_daily_sales_12_weeks.csv"
REQUIRED = {"sku", "sale_date", "units_sold", "revenue"}


def import_daily_csv(csv_path):
    data = pd.read_csv(csv_path, dtype={"sku": "string"})
    missing = REQUIRED - set(data.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

    data = data[list(REQUIRED)].copy()
    data["sku"] = data["sku"].str.strip().str.upper()
    data["sale_date"] = pd.to_datetime(data["sale_date"], errors="coerce").dt.date
    data["units_sold"] = pd.to_numeric(data["units_sold"], errors="coerce")
    data["revenue"] = pd.to_numeric(data["revenue"], errors="coerce")
    if data.isna().any().any():
        raise ValueError("CSV contains blank or invalid SKU, date, units_sold, or revenue values")
    if (data["units_sold"] < 0).any() or (data["revenue"] < 0).any():
        raise ValueError("units_sold and revenue cannot be negative")
    if ((data["units_sold"] % 1) != 0).any():
        raise ValueError("units_sold must contain whole numbers")

    # A daily summary may be represented by multiple input lines; combine them.
    data = data.groupby(["sku", "sale_date"], as_index=False).agg(
        units_sold=("units_sold", "sum"), revenue=("revenue", "sum")
    )
    data["units_sold"] = data["units_sold"].astype(int)
    data["revenue"] = data["revenue"].round(2)

    products = {p.sku.upper(): p.id for p in Product.query.all()}
    unknown = sorted(set(data["sku"]) - set(products))
    if unknown:
        raise ValueError(f"These SKUs are not in products: {', '.join(unknown)}")

    incoming = [
        {"product_id": products[row.sku], "sale_date": row.sale_date,
         "units_sold": int(row.units_sold), "revenue": round(float(row.revenue), 2)}
        for row in data.itertuples(index=False)
    ]
    existing = db.session.execute(
        select(DailyProductSale).where(
            DailyProductSale.product_id.in_([row["product_id"] for row in incoming]),
            DailyProductSale.sale_date.in_([row["sale_date"] for row in incoming]),
        )
    ).scalars().all()
    existing_by_key = {(row.product_id, row.sale_date): row for row in existing}

    inserts = []
    for row in incoming:
        prior = existing_by_key.get((row["product_id"], row["sale_date"]))
        if prior is None:
            inserts.append(DailyProductSale(**row))
        elif prior.units_sold != row["units_sold"] or round(float(prior.revenue), 2) != row["revenue"]:
            raise ValueError(
                f"Existing daily data conflicts for product_id={row['product_id']} "
                f"on {row['sale_date']}; no rows were imported."
            )
    db.session.add_all(inserts)
    db.session.commit()
    return {"rows_in_file": len(data), "inserted": len(inserts), "already_present": len(incoming) - len(inserts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", default=str(DEFAULT_CSV), help="CSV path (defaults to the included 12-week demo dataset)")
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        try:
            result = import_daily_csv(args.csv)
            print("Import complete:", result)
            print("Dataset type: synthetic demonstration data; not real-world sales or model accuracy evidence.")
        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    main()
