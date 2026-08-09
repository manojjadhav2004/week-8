-- ============================================================
-- schema.sql - Relational schema for ecommerce.db
-- ============================================================

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id         INTEGER PRIMARY KEY,
    customer_name        TEXT NOT NULL,
    email                TEXT,
    email_valid          INTEGER,          -- 1/0, flagged during cleaning
    registration_date    TEXT,
    customer_type        TEXT CHECK (customer_type IN ('REGULAR','PREMIUM','VIP'))
);

CREATE TABLE products (
    product_id           INTEGER PRIMARY KEY,
    product_name          TEXT NOT NULL,
    category              TEXT,
    subcategory           TEXT,
    cost_price            REAL
);

CREATE TABLE orders (
    order_id              INTEGER PRIMARY KEY,
    customer_id            INTEGER,
    customer_id_missing    INTEGER,        -- 1/0, flagged during cleaning
    order_date             TEXT,
    is_future_dated        INTEGER,        -- 1/0, flagged during cleaning
    status                 TEXT CHECK (status IN ('PLACED','SHIPPED','DELIVERED','CANCELLED','RETURNED')),
    region_code            TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    item_id                INTEGER PRIMARY KEY,
    order_id                INTEGER NOT NULL,
    product_id              INTEGER NOT NULL,
    quantity                REAL,
    unit_price               REAL,
    discount_percent        REAL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_items_product ON order_items(product_id);
