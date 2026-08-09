"""
Step 1 - Generate Data
-----------------------
Generates 4 raw CSV datasets (customers, products, orders, order_items) with
realistic values via Faker, and deliberately injects data-quality problems
that later pipeline stages (check_raw_data.py, clean_data.py) are meant to
catch:

  - Missing values (NULL customer_id, blank fields)
  - Duplicate records (a handful of exact-duplicate rows in each table)
  - Invalid dates (wrong format, some future-dated orders)
  - Mismatched / orphaned IDs (order_items pointing at non-existent orders)
  - Data type inconsistencies (quantity/discount stored as text in a few rows)

Output: data/raw/customers.csv, products.csv, orders.csv, order_items.csv
"""

import csv
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

N_CUSTOMERS = 600
N_PRODUCTS = 150
N_ORDERS = 1500
N_ORDER_ITEMS = 3500

CATEGORIES = {
    "Electronics": ["Mobiles", "Laptops", "Accessories", "Cameras"],
    "Clothing": ["Men", "Women", "Kids", "Footwear"],
    "Home": ["Furniture", "Kitchen", "Decor", "Bedding"],
    "Books": ["Fiction", "Non-Fiction", "Academic", "Comics"],
}

CUSTOMER_TYPES = ["REGULAR", "PREMIUM", "VIP"]
ORDER_STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
REGION_CODES = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)
TODAY = datetime(2026, 8, 9)  # pipeline "current date" for future-date checks


def random_date(start, end):
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def messy_product_name(name):
    r = random.random()
    if r < 0.15:
        return f"   {name.upper()}   "
    elif r < 0.30:
        return f"{name.lower()}  "
    return name


def messy_email(seed):
    good_email = fake.email()
    if random.random() < 0.02:
        return good_email.replace("@", "") if random.random() < 0.5 else good_email.split("@")[0] + "@"
    return good_email


def generate_customers():
    customers = []
    for i in range(1, N_CUSTOMERS + 1):
        reg_date = random_date(START_DATE, END_DATE)
        customers.append({
            "customer_id": i,
            "customer_name": fake.name(),
            "email": messy_email(i),
            "registration_date": reg_date.strftime("%Y-%m-%d %H:%M:%S"),
            "customer_type": random.choices(CUSTOMER_TYPES, weights=[0.6, 0.3, 0.1])[0],
        })
    # Inject a few exact-duplicate rows (data quality issue)
    for _ in range(6):
        customers.append(dict(random.choice(customers[:N_CUSTOMERS])))
    return customers


def generate_products():
    products = []
    pid = 1
    for category, subcats in CATEGORIES.items():
        for _ in range(N_PRODUCTS // len(CATEGORIES)):
            subcat = random.choice(subcats)
            base_name = f"{fake.word().capitalize()} {subcat[:-1] if subcat.endswith('s') else subcat}"
            products.append({
                "product_id": pid,
                "product_name": messy_product_name(base_name),
                "category": category,
                "subcategory": subcat,
                "cost_price": round(random.uniform(50, 5000), 2),
            })
            pid += 1
    for _ in range(4):
        products.append(dict(random.choice(products)))
    return products


def generate_orders(customers):
    orders = []
    customer_ids = [c["customer_id"] for c in customers[:N_CUSTOMERS]]
    for i in range(1, N_ORDERS + 1):
        order_date = random_date(START_DATE, END_DATE)

        # 2 deliberately future-dated orders (edge case for test_future_date.py)
        if i in (1, 2):
            order_date = TODAY + timedelta(days=random.randint(5, 60))

        cust_id = "" if random.random() < 0.05 else random.choice(customer_ids)

        if random.random() < 0.08:
            date_str = order_date.strftime("%d-%m-%Y")  # wrong format
        else:
            date_str = order_date.strftime("%Y-%m-%d %H:%M:%S")

        orders.append({
            "order_id": i,
            "customer_id": cust_id,
            "order_date": date_str,
            "status": random.choices(ORDER_STATUSES, weights=[0.15, 0.20, 0.45, 0.10, 0.10])[0],
            "region_code": random.choice(REGION_CODES),
        })
    for _ in range(5):
        orders.append(dict(random.choice(orders)))
    return orders


def generate_order_items(orders, products):
    order_items = []
    valid_order_ids = [o["order_id"] for o in orders]
    product_ids = [p["product_id"] for p in products]

    for i in range(1, N_ORDER_ITEMS + 1):
        quantity = random.randint(1, 8)
        if random.random() < 0.03:
            quantity = -abs(quantity)
        if random.random() < 0.005:
            quantity = 0

        unit_price = round(random.uniform(100, 8000), 2)
        discount = round(random.uniform(0, 100), 1)
        if random.random() < 0.003:
            discount = round(random.uniform(101, 150), 1)

        # ~1% of rows: numeric fields stored as text (data type inconsistency)
        qty_val = str(quantity) if random.random() < 0.01 else quantity
        discount_val = f"{discount}%" if random.random() < 0.01 else discount

        order_items.append({
            "item_id": i,
            "order_id": random.choice(valid_order_ids),
            "product_id": random.choice(product_ids),
            "quantity": qty_val,
            "unit_price": unit_price,
            "discount_percent": discount_val,
        })

    # Orphaned order_items (order_id not in orders) -- referential integrity issue
    max_order_id = max(valid_order_ids)
    for j in range(8):
        order_items.append({
            "item_id": N_ORDER_ITEMS + j + 1,
            "order_id": max_order_id + 100 + j,
            "product_id": random.choice(product_ids),
            "quantity": random.randint(1, 5),
            "unit_price": round(random.uniform(100, 8000), 2),
            "discount_percent": round(random.uniform(0, 100), 1),
        })

    for _ in range(6):
        order_items.append(dict(random.choice(order_items[:N_ORDER_ITEMS])))

    return order_items


def write_csv(rows, filepath, fieldnames):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fieldnames})


def main():
    print("Generating customers...")
    customers = generate_customers()
    write_csv(customers, "data/raw/customers.csv",
              ["customer_id", "customer_name", "email", "registration_date", "customer_type"])

    print("Generating products...")
    products = generate_products()
    write_csv(products, "data/raw/products.csv",
              ["product_id", "product_name", "category", "subcategory", "cost_price"])

    print("Generating orders...")
    orders = generate_orders(customers)
    write_csv(orders, "data/raw/orders.csv",
              ["order_id", "customer_id", "order_date", "status", "region_code"])

    print("Generating order_items...")
    order_items = generate_order_items(orders, products)
    write_csv(order_items, "data/raw/order_items.csv",
              ["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent"])

    print(f"\nDone. Raw files written to data/raw/")
    print(f"  customers.csv    : {len(customers)} rows")
    print(f"  products.csv     : {len(products)} rows")
    print(f"  orders.csv       : {len(orders)} rows")
    print(f"  order_items.csv  : {len(order_items)} rows")


if __name__ == "__main__":
    main()
