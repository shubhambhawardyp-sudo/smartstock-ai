CREATE DATABASE IF NOT EXISTS smartstock_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE smartstock_db;

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
);

CREATE TABLE suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    contact_name VARCHAR(120),
    email VARCHAR(254),
    phone VARCHAR(40)
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    description TEXT,
    category_id INT NOT NULL,
    supplier_id INT NULL,
    cost_price DECIMAL(12, 2) NOT NULL DEFAULT 0 CHECK (cost_price >= 0),
    selling_price DECIMAL(12, 2) NOT NULL DEFAULT 0 CHECK (selling_price >= 0),
    stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    reorder_threshold INT NOT NULL DEFAULT 5 CHECK (reorder_threshold >= 0),
    lead_time_days INT NOT NULL DEFAULT 7,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_products_category (category_id),
    INDEX ix_products_name (name),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

CREATE TABLE sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(40) NOT NULL UNIQUE,
    sold_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
    INDEX ix_sales_sold_at (sold_at)
);

CREATE TABLE sale_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12, 2) NOT NULL CHECK (unit_price >= 0),
    line_total DECIMAL(12, 2) NOT NULL CHECK (line_total >= 0),
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

CREATE TABLE stock_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    movement_type ENUM('IN', 'OUT', 'ADJUSTMENT', 'SALE') NOT NULL,
    quantity INT NOT NULL,
    reason VARCHAR(255) NOT NULL,
    reference VARCHAR(80),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_movement_product (product_id),
    INDEX ix_movement_created (created_at),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

CREATE TABLE daily_product_sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    sale_date DATE NOT NULL,
    units_sold INT NOT NULL DEFAULT 0,
    revenue DECIMAL(14, 2) NOT NULL DEFAULT 0,
    UNIQUE KEY uq_daily_product_date (product_id, sale_date),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE demand_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_units DOUBLE NOT NULL,
    model_version VARCHAR(60) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_prediction_product_date_version (
        product_id,
        forecast_date,
        model_version
    ),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE pipeline_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME NULL,
    status VARCHAR(20) NOT NULL,
    records_processed INT NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE model_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_version VARCHAR(60) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(40) NOT NULL,
    metric_value DOUBLE NOT NULL,
    evaluated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'staff') NOT NULL DEFAULT 'staff',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME NULL
);

INSERT INTO categories (name, description)
VALUES
    ('Beverages', 'Drinks and refreshments'),
    ('Pantry', 'Shelf-stable food'),
    ('Stationery', 'Office and college supplies'),
    ('Cleaning', 'Household cleaning goods');

INSERT INTO suppliers (name, contact_name, email, phone)
VALUES
    ('Northstar Wholesale', 'A. Patel', 'orders@northstar.example', '+1-555-0101'),
    ('Campus Supply Co.', 'R. Kim', 'sales@campussupply.example', '+1-555-0133');

INSERT INTO products (
    sku,
    name,
    description,
    category_id,
    supplier_id,
    cost_price,
    selling_price,
    stock_quantity,
    reorder_threshold,
    lead_time_days
)
VALUES
    ('BEV-001', 'Sparkling Water', 'Lime 12-pack', 1, 1, 4.50, 7.99, 42, 12, 3),
    ('PAN-014', 'Oat Milk', 'Unsweetened 1L carton', 2, 1, 2.10, 3.99, 8, 10, 5),
    ('STA-022', 'Campus Notebook', 'Ruled A5 notebook', 3, 2, 1.20, 2.99, 86, 20, 4),
    ('CLN-008', 'Surface Cleaner', 'Citrus multi-surface spray', 4, 2, 3.25, 5.49, 5, 8, 7),
    ('PAN-031', 'Granola Bar', 'Honey almond 6-pack', 2, 1, 2.80, 4.99, 27, 10, 5),
    ('BEV-017', 'Cold Brew Coffee', 'Ready-to-drink 250ml', 1, 1, 1.75, 3.49, 18, 9, 3);
