# SmartStock AI

SmartStock AI is a Flask inventory management demonstration backed by MySQL. It supports a product catalog, stock adjustments, sales, inventory analytics, a CSV-to-database ETL pipeline, and a seven-day demand forecast. The project is intended for local learning and demonstration; it is not a production-ready, multi-user system.

For the formal requirements, technology stack, full project structure, and database diagram, see [`docs/SRS.md`](docs/SRS.md).

## Database connection at a glance

The application talks to MySQL through this chain:

```text
Browser (HTML/JavaScript)
  -> Flask API routes
  -> SQLAlchemy ORM
  -> PyMySQL driver
  -> MySQL Server (usually 127.0.0.1:3306)
  -> smartstock_db schema and tables
```

The database server must be installed and running separately from this Python application. MySQL Workbench is a GUI client for the server; the project does not connect to Workbench itself.

### What each database file/configuration does

| Item | Purpose |
|---|---|
| `schema.sql` | Creates the `smartstock_db` database, its tables, constraints and indexes, then inserts demo categories, suppliers and products. Run it once against your MySQL server. |
| `models/database_models.py` | SQLAlchemy definitions for the same operational and analytics tables used by the Flask code. |
| `.env` | Local-only connection settings and Flask secret. This file is ignored by Git and must contain your actual local credentials. |
| `.env.example` | Safe template showing the required settings; its values are placeholders and will not authenticate. |
| `app.py` | Loads `.env`, configures SQLAlchemy and registers API routes. Running `python app.py` also calls `db.create_all()`; it can create missing tables only after the named database already exists, and it does not insert the demo seed rows. |
| `config.py` | Reads `DATABASE_URL`, `SECRET_KEY`, and optional `MODEL_PATH`; configures SQLAlchemy connection-pool checks. |

### Windows setup

#### 1. Start MySQL Server

Install MySQL Server 8.0 and make sure its Windows service is running (commonly named `MySQL80`). Workbench is optional but makes running the SQL file easier. The connection name shown in Workbench is only a saved client profile; the URL below uses the MySQL account username, password, host, and port.

#### 2. Create and seed the database

In MySQL Workbench, connect to your local server, open `schema.sql` from this project, then click the lightning-bolt execute button. The script creates `smartstock_db` and inserts four sample categories, two suppliers and six products. It is designed as a first-time seed script; do not repeatedly run it after data has been added, because the sample `INSERT` statements can conflict with existing unique SKUs/categories.

Alternatively, if MySQL command-line client `mysql.exe` is on PATH, open **Command Prompt** (not the default PowerShell prompt), change to the project folder, then run:

```powershell
mysql -u root -p < schema.sql
```

`MySQL Shell` is a separate client. Its default prompt may be JavaScript; switch to SQL mode with `\sql` before SQL commands, or use Workbench / the `mysql` command above.

#### 3. Configure the project connection

From the project folder, create your local env file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace the placeholder username/password with the account that can access `smartstock_db`. For example, if your MySQL account is `root`, the server is on this computer, and you chose a password during MySQL Server setup:

```dotenv
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/smartstock_db?charset=utf8mb4
SECRET_KEY=replace-this-with-a-long-random-local-value
```

Replace `YOUR_PASSWORD`; do not include the angle brackets. The username is the part before the colon (`root` in this example). The host is commonly `127.0.0.1` or `localhost`, and the default MySQL port is `3306`. Use the exact username/password accepted by your MySQL server. Do not paste real credentials into chat or commit `.env`.

If a password contains URL-reserved characters such as `@`, `:`, `/`, `#`, or `%`, URL-encode those characters in the URL. For example, encode `@` as `%40`. Do not put quotes around the complete `DATABASE_URL` line. A simple password is easier for a local beginner setup.

#### 4. Install Python dependencies and run

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. The first app start runs SQLAlchemy `create_all()` to create any missing tables inside the configured database. Running `schema.sql` first is recommended because it also creates the named database and seeds its example records.

### Verify and troubleshoot the connection

Open <http://127.0.0.1:5000/health/db>. A successful connection returns JSON containing `"database":"connected"`.

| Symptom | Check |
|---|---|
| `database unavailable` / connection refused | Confirm MySQL Server service is running and host/port in `DATABASE_URL` are correct. |
| Access denied | Check the MySQL username and password; these are not necessarily the same as your Windows login or Workbench connection name. |
| Unknown database | Run `schema.sql` against the intended local MySQL server and confirm the database is named `smartstock_db`. |
| App still uses an old password | Stop Flask with Ctrl+C, save `.env`, then start `python app.py` again. `.env` is loaded when the process starts. |
| Categories are missing | Confirm the API connection works and the seed statements in `schema.sql` ran. Check <http://127.0.0.1:5000/api/categories>. |

The database health route returns safe hints, not credentials. For a failed application request, inspect the terminal where `python app.py` is running. Never share a screenshot or log containing your real password.

## Main features

- Product, category and supplier catalog with paginated product search.
- Stock adjustment history; each adjustment records a reason.
- Sales written as invoices and sale items, with stock decrement and movement records in one transaction. Insufficient stock causes the transaction to roll back.
- Dashboard totals, sales summaries, inventory value, stock alerts and reorder suggestions.
- CSV ETL that aggregates daily SKU sales and loads product-day summaries.
- Random Forest demand model compared with a historical-average baseline; chronological evaluation records MAE/RMSE and saves a joblib artifact.
- Rule-based stock risk/reorder guidance using forecast demand and supplier lead time. This is a transparent rule, not a trained classifier.

## Demo data, import and forecasting

The checked-in `data/sample_daily_sales_12_weeks.csv` contains synthetic daily sales history for the six seeded product SKUs. It is demonstration data, not evidence of real-world model accuracy.

Import its daily summaries after `schema.sql` has been loaded and the `.env` connection works:

```powershell
python -m pipelines.import_daily_csv
```

The importer expects a CSV with product SKU, sale date, units sold and revenue columns; SKUs must already exist in `products`. Existing identical product/date rows are skipped; conflicting values are rejected to avoid silently replacing data. To use a different file, pass its path as the command's final argument.

The trainer requires at least 14 days of history for at least one product. With the included 12-week dataset imported, train/evaluate the model:

```powershell
python -m ml.train
```

Training uses chronological holdout evaluation and writes the model artifact under `ml/artifacts/` by default. `python -m pipelines.run_pipeline` is a separate ETL path: it reads completed invoices and line items already stored in MySQL, aggregates them by product/day, and upserts those summaries. It does not read the included daily CSV or `sample_sales.csv`.

If you have fewer than 14 days of sales history, the project also provides an explicitly synthetic data generator for demonstration only:

```powershell
python -m ml.generate_demo_data --days 120
python -m ml.train
```

Generated data is synthetic; model scores trained on it are not real-world accuracy evidence. To run the ETL pipeline using actual sales recorded through the app/API, use:

```powershell
python -m pipelines.run_pipeline
```

Finally, in the dashboard click **Generate forecast**. The API stores seven days of predictions per product in `demand_predictions`. If your source is the 12-week daily CSV, import it with `pipelines.import_daily_csv` before training.

## API quick reference

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health/db` | Check MySQL connectivity. |
| `GET` | `/api/dashboard?days=30` | Dashboard metrics and chart data. |
| `GET`, `POST` | `/api/products` | List/search or create products. |
| `GET`, `PUT`, `DELETE` | `/api/products/<id>` | Read, update or delete a product. |
| `POST` | `/api/products/<id>/adjust` | Apply a signed stock adjustment with a reason. |
| `GET`, `POST` | `/api/categories` | List or create categories. |
| `GET`, `POST` | `/api/suppliers` | List or create suppliers. |
| `GET`, `POST` | `/api/sales` | List recent sales or record a sale. |
| `GET` | `/api/movements` | List recent stock movement history. |
| `GET` | `/api/reorder` | Get risk/reorder recommendations. |
| `GET` | `/api/predictions` | List saved forecast rows. |
| `POST` | `/api/predictions/generate` | Generate forecast rows from the model artifact. |
| `GET` | `/api/pipeline/status` | Read the last ETL run. |

Example sale request body:

```json
{"items":[{"product_id":1,"quantity":2},{"product_id":5,"quantity":1}]}
```

## Tests

The test suite uses a separate database URL. Set `TEST_DATABASE_URL` to a disposable MySQL test schema before running `pytest -q`. Never point it at a production or personal database; tests can create/clear test tables.

## Security and scope

The `users` table is currently a schema placeholder: the app has no login, password verification, or role enforcement. Keep this demonstration bound to localhost. Before exposing it to other users or deploying it, implement authentication and authorization, CSRF protection, secure secret management, backups, migrations, and production WSGI deployment settings. Bootstrap, Chart.js and the browser UI's other CDN assets require internet access in the browser.
