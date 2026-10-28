# SmartStock AI — Software Requirements Specification

**Version:** 1.1
**Status:** Student project specification  
**System type:** Local web application with MySQL persistence and a batch demand-forecasting component

## 1. Purpose and scope

SmartStock AI is a prototype for a small store that needs to maintain a product catalog, record stock changes and sales, review inventory health, and explore short-term product demand estimates. This document records the current implementation and its intended behavior so that the system can be reviewed, demonstrated, and extended.

The current release is a local store-management application with username/password sign-in. Accounts are created by a trusted operator through `create_user.py`; there is no public self-registration page. Each authenticated account currently has the same application permissions. Purchase-order processing, supplier communications, account recovery, and production deployment controls are outside the current scope.

### 1.1 Goals

- Maintain product, category, and supplier records with relational integrity.
- Keep the product stock balance consistent with sales and manual adjustments.
- Report inventory value, sales summaries, reorder risk, and demand forecasts.
- Import daily sales history through a repeatable CSV/ETL workflow.
- Persist source operational records and analytical results in MySQL.

### 1.2 Stakeholders and users

| Role | Current interaction |
|---|---|
| Store operator / account holder | Signs in to manage catalog, stock, sales, dashboard analytics, and forecasts. |
| System maintainer | Creates accounts, configures the local MySQL connection, runs schema/migration/ETL/model commands, and maintains the Flask code. |

## 2. Technology stack

| Layer | Technology | Responsibility |
|---|---|---|
| User interface | HTML, CSS, JavaScript, Bootstrap 5, Chart.js | Dashboard, product forms, charts, fetch calls to JSON API. Bootstrap and Chart.js are currently loaded from a CDN. |
| Web server / API | Python 3.11+, Flask 3.x, Flask-Login, Flask-WTF | Serves the sign-in page, authenticated dashboard and API endpoints; protects browser writes with CSRF tokens. |
| Password security | Werkzeug password hashing | Stores and verifies password hashes; plaintext passwords are not stored. |
| ORM / database access | Flask-SQLAlchemy 3.x, SQLAlchemy 2.x, PyMySQL | Maps Python models to relational tables and sends SQL to MySQL through the PyMySQL DB-API driver. |
| Database | MySQL Server 8.0, InnoDB, `utf8mb4` | Stores catalog, stock, sales, movement history, daily summaries, predictions, ETL logs and model metrics. |
| Configuration | `python-dotenv` and process environment | Loads local `.env` settings at application startup. |
| ETL and modeling | pandas, NumPy, scikit-learn, joblib | Reads/aggregates sales history, engineers time-series features, trains/evaluates a Random Forest and persists a model artifact. |
| Quality checks | pytest | Test suite; configure a disposable `TEST_DATABASE_URL`. |

Exact dependency version ranges are recorded in `requirements.txt`.

## 3. System architecture and database connection

### 3.1 Request/data flow

```text
Browser
  | HTTP (dashboard assets and JSON requests)
  v
Flask app.py
  | route blueprints: auth.py, products.py, sales.py, analytics.py, predictions.py
  | Flask-Login session + Flask-WTF CSRF protection
  v
Services and SQLAlchemy models
  | Flask-SQLAlchemy / SQLAlchemy engine
  | PyMySQL driver
  v
MySQL Server :3306
  +-- smartstock_db
      +-- operational tables (catalog, stock, sales)
      +-- analytical tables (daily sales, predictions, metrics)

Batch path: CSV -> pipelines.extract/transform/load -> daily_product_sales
Forecast path: daily_product_sales -> ml.train -> joblib artifact
              -> forecasting service -> demand_predictions
```

### 3.2 Connection configuration

At import/startup, `app.py` loads `.env` from the directory containing `app.py`. `config.py` reads `DATABASE_URL` and passes it to Flask-SQLAlchemy. The SQLAlchemy MySQL dialect uses PyMySQL to connect to the MySQL server. The application does not connect to MySQL Workbench; Workbench is a separate GUI client for the same MySQL server.

Expected URL form:

```text
mysql+pymysql://<mysql_user>:<password>@<host>:3306/smartstock_db?charset=utf8mb4
```

Example with placeholders only:

```dotenv
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/smartstock_db?charset=utf8mb4
SECRET_KEY=replace-with-a-long-random-value
```

`root` is only an example; use the MySQL account configured on the server. Replace `YOUR_PASSWORD` with that account's password. The password is part of the URL and must be URL-encoded if it contains reserved URL characters. Do not quote the whole value, and do not commit `.env`.

### 3.3 Database initialization sequence

1. Install/start MySQL Server and connect to the intended server/port.
2. Execute the current `schema.sql` once in MySQL Workbench or with the MySQL CLI. It creates the database, current tables and sample rows. For an older database, `create_user.py` adds the login fields automatically if the MySQL account has `ALTER TABLE` permission; otherwise execute `migrations/002_user_auth.sql` once in Workbench.
3. Copy `.env.example` to `.env`; set `DATABASE_URL` for that server/schema and a persistent random `SECRET_KEY` for browser sessions.
4. Install Python requirements. Run `python create_user.py`; it checks the database connection and user-table schema, then prompts for the first username/password. Passwords must be at least 12 characters and are stored as hashes.
5. Run `python app.py`, open `http://127.0.0.1:5000/login`, and sign in. Check `http://127.0.0.1:5000/health/db` for `database: connected`; this safe health endpoint does not require sign-in.

The app's `db.create_all()` attempts to create absent tables after connecting, but it cannot create `smartstock_db`, migrate existing tables, or populate seed categories/products. Use `schema.sql` for an initial database and sample content; use the one-time migration for existing databases. Avoid re-running the seed script over a database that already contains those unique sample values.

## 4. Functional requirements

| ID | Requirement | Current implementation / acceptance condition |
|---|---|---|
| FR-01 | View inventory dashboard | Dashboard API returns product count, stock units, inventory value, revenue, chart data, and alerts. |
| FR-02 | Maintain product catalog | API supports product listing/search, create, detail, update, and delete; category and supplier foreign keys must be valid. |
| FR-03 | Prevent negative stock/price values | Product validation and MySQL check constraints reject invalid negative values. |
| FR-04 | Record stock adjustment | A signed nonzero quantity and reason update the product balance and append a stock movement in the same operation. |
| FR-05 | Record a dated sale | Sales screen records product, positive quantity, and sale date. A sale dated today checks and decreases stock and adds a stock movement; a past-date entry adds invoice, line-item, and daily demand history without changing today's stock. All sale and daily-summary writes are atomic. Future sale dates and invalid quantities are rejected. |
| FR-06 | Review stock movement | API returns latest movement history, including product, type, quantity, reason and timestamp. |
| FR-07 | Review stock risk/reorder | API/dashboard use forecast daily demand, supplier lead time, safety stock and current stock to calculate risk and suggested reorder quantity. |
| FR-08 | Import daily sales summaries | CSV import validates/maps SKU/date/units/revenue, aggregates repeated SKU/date rows, and inserts daily summaries idempotently while rejecting conflicting existing values. |
| FR-09 | Train/evaluate demand model | Model workflow builds time-series features, uses chronological holdout evaluation, compares Random Forest against a historical mean baseline, and stores model/metrics. |
| FR-10 | Generate future estimates | Prediction API uses the saved model to produce seven daily estimates per product and persists them with a model version. |
| FR-11 | Check DB health | `/health/db` performs a simple database query and returns connection state with a safe diagnostic hint. |
| FR-12 | Record ETL run state | Pipeline records start/finish, status, processed record count, and error message in `pipeline_logs`. |
| FR-13 | Sign in and sign out | A user with an active account can sign in using username/password and sign out. The application stores a password hash, records account creation/last sign-in, and protects dashboard/API routes behind an authenticated session. Public self-registration is not provided. |
| FR-14 | Protect browser writes | Login, logout and state-changing API requests require a valid CSRF token. Session cookies are HTTP-only and use `SameSite=Lax`. |

## 5. Non-functional requirements

- **NFR-01 Reliability:** Sales stock and invoice changes must be transactional. Invalid input must return an API error without partial stock updates.
- **NFR-02 Data integrity:** Primary keys, foreign keys, unique indexes/constraints and check constraints must enforce core relationships and values in MySQL.
- **NFR-03 Configuration safety:** Database credentials and session secret are loaded from environment settings; local `.env` is not versioned. Missing/example session secrets are replaced by a temporary random key for local development; operators should set a persistent random key.
- **NFR-04 Operability:** A developer can run the app locally and diagnose database availability using `/health/db` and the application terminal.
- **NFR-05 Maintainability:** HTTP endpoints, domain services, ORM models, ETL stages, ML workflows, and UI assets are separated into named modules.
- **NFR-06 Forecast transparency:** Forecast evaluation must use time-ordered holdout data; generated synthetic data must be identified as synthetic and its metrics must not be claimed as real-world performance.
- **NFR-07 Scope/security:** The current build is for localhost use. It has sign-in and CSRF protection but does not enforce distinct user roles or provide password recovery. Before production use it needs HTTPS and secure cookies, role-based authorization, account recovery, a migration/backup strategy, and a production server.

## 6. Database schema

The schema is defined in `schema.sql`; the corresponding ORM declarations are in `models/database_models.py`. IDs are auto-incrementing integer primary keys. Timestamps are stored as MySQL `DATETIME`; sales dates for summaries and forecasts use `DATE`. Monetary values use `DECIMAL` in operational tables to avoid floating-point currency storage.

### 6.1 Entity relationship diagram (Mermaid)

The following Mermaid ER diagram can be rendered in Mermaid-compatible Markdown viewers or pasted into Mermaid Live Editor. It documents the schema's central entities and foreign-key relationships.

```mermaid
erDiagram
    CATEGORIES ||--o{ PRODUCTS : categorizes
    SUPPLIERS o|--o{ PRODUCTS : supplies
    PRODUCTS ||--o{ SALE_ITEMS : sold_as
    SALES ||--|{ SALE_ITEMS : contains
    PRODUCTS ||--o{ STOCK_MOVEMENTS : changes
    PRODUCTS ||--o{ DAILY_PRODUCT_SALES : summarized_as
    PRODUCTS ||--o{ DEMAND_PREDICTIONS : forecast_for

    CATEGORIES {
        int id PK
        varchar name UK
        varchar description
    }
    SUPPLIERS {
        int id PK
        varchar name
        varchar contact_name
        varchar email
        varchar phone
    }
    PRODUCTS {
        int id PK
        varchar sku UK
        varchar name
        text description
        int category_id FK
        int supplier_id FK
        decimal cost_price
        decimal selling_price
        int stock_quantity
        int reorder_threshold
        int lead_time_days
        datetime created_at
        datetime updated_at
    }
    SALES {
        int id PK
        varchar invoice_number UK
        datetime sold_at
        decimal total_amount
    }
    SALE_ITEMS {
        int id PK
        int sale_id FK
        int product_id FK
        int quantity
        decimal unit_price
        decimal line_total
    }
    STOCK_MOVEMENTS {
        int id PK
        int product_id FK
        enum movement_type
        int quantity
        varchar reason
        varchar reference
        datetime created_at
    }
    DAILY_PRODUCT_SALES {
        int id PK
        int product_id FK
        date sale_date
        int units_sold
        decimal revenue
    }
    DEMAND_PREDICTIONS {
        int id PK
        int product_id FK
        date forecast_date
        double predicted_units
        varchar model_version
        datetime created_at
    }
    PIPELINE_LOGS {
        int id PK
        datetime started_at
        datetime finished_at
        varchar status
        int records_processed
        text error_message
    }
    MODEL_METRICS {
        int id PK
        varchar model_version
        varchar model_name
        varchar metric_name
        double metric_value
        datetime evaluated_at
    }
    USERS {
        int id PK
        varchar username UK
        varchar password_hash
        enum role
        boolean is_active
        datetime created_at
        datetime last_login_at
    }
```

`PIPELINE_LOGS`, `MODEL_METRICS`, and `USERS` have no foreign-key relationship in the current implementation. `USERS` stores account identity, password hash, active state, role label and login timestamps. The role column is not currently used to distinguish permissions. The `SALE_ITEMS` relationship to `SALES` is mandatory in practice: each sale item references exactly one sale; each sale created by the application contains one or more items.

### 6.2 Table responsibilities and important constraints

| Table | Responsibility | Integrity rules |
|---|---|---|
| `categories` | Product classification. | `name` is unique and required. |
| `suppliers` | Supplier contact information. | A supplier may have many products; deleting a supplier sets those products' supplier reference to `NULL`. |
| `products` | Catalog and current stock balance. | Unique required SKU; required category; nonnegative cost, selling price, stock and reorder threshold; category deletion is restricted while products refer to it. |
| `sales` | Sale/invoice header and total. | Unique invoice number. |
| `sale_items` | Product lines per sale. | References one sale and one product; sale deletion cascades to its lines; product deletion is restricted if used in a sale. SQL enforces positive quantity and nonnegative prices/totals. |
| `stock_movements` | Auditable stock change events. | Product deletion is restricted while movement history exists; movement type is `IN`, `OUT`, `ADJUSTMENT`, or `SALE`. |
| `daily_product_sales` | One product's aggregated sales for one day. | Unique `(product_id, sale_date)`; product deletion cascades to summaries. |
| `demand_predictions` | Forecast by product, forecast day and model. | Unique `(product_id, forecast_date, model_version)`; product deletion cascades to predictions. |
| `pipeline_logs` | ETL run status, count, and error details. | No product relationship. |
| `model_metrics` | Evaluation metric values by model/run label. | No product relationship. |
| `users` | Sign-in identity and account state. | Unique username; password hash only; active flag; account creation and last login timestamps. Role values are stored but do not currently grant different permissions. |

### 6.3 Database behavior and data lifecycle

- A sale dated today decrements `products.stock_quantity`, inserts a `sales` row, one or more `sale_items`, and a `SALE` movement per sold product. Past-date sales entered to backfill history create invoice and line-item records and update `daily_product_sales` without changing current stock. Sale rows, daily summaries, stock and movement records are committed together.
- A manual adjustment changes the balance and inserts an `ADJUSTMENT` movement with a reason.
- The CSV importer loads product-day totals to `daily_product_sales`; daily summaries are the main history input to model training and forecasts.
- Forecast rows are generated per product/date and identify the model version. Regenerating the same model's current seven-day horizon replaces those horizon rows before committing fresh results.
- Reorder guidance is calculated from current stock and lead-time demand, using forecast data when present; it is a rule-based recommendation, not an extra database entity or trained classifier.

## 7. API interface summary

The JSON API is served under `/api`. The dashboard and API require a signed-in session. State-changing browser requests include the CSRF token supplied by the dashboard page; `/health/db` is a safe unauthenticated connectivity check.

| Method | Endpoint | Request/response intent |
|---|---|---|
| `GET`, `POST` | `/login` | Render sign-in page or authenticate username/password. |
| `POST` | `/logout` | End the signed-in session; requires a CSRF token. |
| `GET` | `/health/db` | Database connectivity status. |
| `GET`, `POST` | `/login` | Render sign-in page or authenticate an active username/password account. |
| `POST` | `/logout` | Sign out and clear the authenticated session. Requires a CSRF token. |
| `GET` | `/api/products?q=<term>&page=<n>` | Product search and paginated list. |
| `POST` | `/api/products` | Create product from SKU/name/category and optional price/stock fields. |
| `GET`, `PUT`, `DELETE` | `/api/products/<id>` | Read, update or delete a product. |
| `GET`, `POST` | `/api/categories` | List or add a category. |
| `GET`, `POST` | `/api/suppliers` | List or add a supplier. |
| `POST` | `/api/products/<id>/adjust` | Apply signed quantity with a reason. |
| `GET` | `/api/movements` | Latest stock movements. |
| `POST` | `/api/sales` | Record a sale from `{"sale_date":"2026-10-27","items":[{"product_id":1,"quantity":2}]}`. `sale_date` defaults to today; past dates backfill demand history without changing current stock. |
| `GET` | `/api/sales` | List recent invoices and their product, SKU, quantity, price and date. |
| `GET` | `/api/dashboard?days=30` | Dashboard cards, chart series and alerts. |
| `GET` | `/api/reorder` | Risk and suggested reorder recommendations. |
| `GET`, `POST` | `/api/predictions`, `/api/predictions/generate` | List saved forecasts or generate next seven days. |
| `GET` | `/api/pipeline/status` | Latest ETL status. |

Create accounts from the project folder with `python create_user.py`. This command asks for a username and password in the terminal and stores a password hash; accounts are not created through a public registration page.

## 8. Project structure

```text
smartstock-ai/
├── app.py                         # Flask app factory, .env loading, health route, startup
├── config.py                      # Environment-backed settings and SQLAlchemy options
├── requirements.txt               # Python dependencies
├── schema.sql                     # MySQL database, table, and demo seed script
├── create_user.py                 # Securely create a local account with a password hash
├── migrations/
│   └── 002_user_auth.sql           # Add auth fields to an existing database
├── seed_data.sql                  # Additional seed SQL (inspect before re-running)
├── sample_sales.csv               # Small source CSV used by the ETL pipeline
├── data/
│   └── sample_daily_sales_12_weeks.csv # Synthetic 12-week product-day history
├── models/
│   ├── database_models.py          # SQLAlchemy relational models
│   └── demand_model.py             # Forecast feature/model helpers
├── routes/
│   ├── auth.py                     # Sign-in and sign-out routes
│   ├── products.py                 # Product/category/supplier/stock APIs
│   ├── sales.py                    # Sales APIs
│   ├── analytics.py                # Dashboard analytics API
│   └── predictions.py              # Forecast and reorder APIs
├── services/
│   ├── inventory_service.py        # Validation, sale transaction, stock adjustment
│   └── forecasting_service.py      # Forecast persistence and risk/reorder calculations
├── pipelines/
│   ├── extract.py                  # Read source sales data
│   ├── transform.py                # Validate and aggregate product-day data
│   ├── load.py                     # Persist daily summary rows
│   ├── import_daily_csv.py         # Import the 12-week daily CSV directly
│   └── run_pipeline.py             # Orchestrate ETL and log run
├── ml/
│   ├── train.py                    # Train and evaluate model
│   ├── evaluate.py                 # Evaluation helpers/entry point
│   ├── generate_demo_data.py       # Explicit synthetic-data generator
│   └── artifacts/                  # Saved joblib model artifact
├── templates/
│   ├── index.html                  # Authenticated dashboard
│   └── login.html                  # Sign-in page
├── static/                         # Browser JavaScript and CSS
├── tests/                          # pytest tests (use a separate test database)
├── docs/
│   └── SRS.md                      # This specification and Mermaid ER diagram
├── .env.example                    # Safe configuration template
└── README.md                       # Setup and operator guide
```

The local `.env`, Python virtual environment, and cache files are not part of the committed structure.

## 9. Assumptions, limitations, and future work

### Current assumptions and limitations

- MySQL Server is available locally on the configured host and port; the application database is pre-created.
- The product's current stock is stored as a balance and changed through application operations; the movement table provides the audit trail.
- A forecast is only an estimate. Short, synthetic, or sparse histories can produce weak results.
- Generated sample sales are synthetic and should only be used to demonstrate pipeline behavior.
- Role-based permission differences, password recovery, supplier purchase workflows, and production operations are not implemented.

### Potential extensions

- Role-based authorization, password recovery, audit identity, stronger session policy for hosted deployments, and secure password reset.
- Database migrations/versioning, automated backup/restore, and integration/deployment configuration.
- Purchase orders and receiving workflows linked to suppliers and stock movements.
- Promotion, holiday, price-change and stockout features in forecasting; forecast intervals and model monitoring.
- More complete reporting and permissions for multi-store operation.
