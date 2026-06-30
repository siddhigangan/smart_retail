import os
import csv
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from app.database.session import Base
# Import models to register them on Base metadata
from app.models import Product, Bill, BillItem, Customer, Shelf, InventoryMapping, RefillLog

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL not set in .env")
    exit(1)

engine = create_engine(DATABASE_URL)

def run_seed():
    # Ensure tables exist
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

    # 1. Clean existing database tables
    tables = [
        "bill_items",
        "bills",
        "customers",
        "refill_logs",
        "inventory_mappings",
        "shelves",
        "products"
    ]
    
    with engine.connect() as conn:
        print("Truncating existing tables...")
        for table in tables:
            try:
                res = conn.execute(text(f"SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = '{table}');"))
                if res.scalar():
                    conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
                    print(f"  [Truncated] {table}")
            except Exception as e:
                print(f"  [Skip/Error] Truncating {table}: {e}")
        conn.commit()

        # 2. Run products seed SQL
        print("\nSeeding products table from SQL file...")
        sql_path = "smart_retail_500_product_dataset_nagpur/seed_products_500_current_schema.sql"
        if not os.path.exists(sql_path):
            print(f"Error: {sql_path} does not exist.")
            return

        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        statements = sql_content.split("\n")
        sql_count = 0
        for line in statements:
            line = line.strip()
            if not line or line.startswith("--"):
                continue
            conn.execute(text(line))
            sql_count += 1
        conn.commit()
        print(f"Successfully executed {sql_count} product insert commands.")

        # Load product ids and barcodes
        res = conn.execute(text("SELECT id, barcode FROM products;"))
        barcode_to_id = {row[1]: row[0] for row in res}
        print(f"Loaded {len(barcode_to_id)} products from database.")

        # 3. Seed customers
        print("\nSeeding customers table from CSV...")
        cust_path = "smart_retail_500_product_dataset_nagpur/customers_synthetic.csv"
        valid_customer_ids = set()
        seen_phones = set()
        
        with open(cust_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cust_id = int(row["customer_id"])
                name = row["customer_name"].strip()
                phone = row["whatsapp_number"].strip()
                points = int(row["loyalty_points"])
                
                if phone in seen_phones:
                    continue
                seen_phones.add(phone)
                valid_customer_ids.add(cust_id)
                
                conn.execute(
                    text("INSERT INTO customers (id, name, phone, total_points, created_at) VALUES (:id, :name, :phone, :points, NOW())"),
                    {"id": cust_id, "name": name, "phone": phone, "points": points}
                )
        conn.commit()
        print(f"Seeded {len(valid_customer_ids)} customers.")

        # 4. Seed bills
        print("\nSeeding bills table from CSV...")
        bills_path = "smart_retail_500_product_dataset_nagpur/bills_synthetic.csv"
        bill_count = 0
        
        with open(bills_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bill_id = int(row["bill_id"])
                bill_date = row["bill_date"]
                cust_id = int(row["customer_id"]) if row["customer_id"] else None
                cust_name = row["customer_name"].strip() if row["customer_name"] else None
                phone = row["whatsapp_number"].strip() if row["whatsapp_number"] else None
                total_amount = Decimal(row["total_amount"])
                
                # Check foreign key constraint for customer_id
                if cust_id not in valid_customer_ids:
                    cust_id = None
                
                conn.execute(
                    text("""INSERT INTO bills (id, total_amount, created_at, customer_id, customer_name, customer_phone)
                            VALUES (:id, :total_amount, :created_at, :customer_id, :customer_name, :customer_phone)"""),
                    {
                        "id": bill_id,
                        "total_amount": total_amount,
                        "created_at": bill_date,
                        "customer_id": cust_id,
                        "customer_name": cust_name,
                        "customer_phone": phone
                    }
                )
                bill_count += 1
        conn.commit()
        print(f"Seeded {bill_count} bills.")

        # 5. Seed bill items
        print("\nSeeding bill_items table from CSV...")
        items_path = "smart_retail_500_product_dataset_nagpur/bill_items_synthetic.csv"
        item_count = 0
        
        with open(items_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bill_id = int(row["bill_id"])
                barcode = row["product_barcode"].strip()
                qty = int(row["quantity"])
                price = Decimal(row["unit_price"])
                subtotal = Decimal(row["subtotal"])
                
                prod_id = barcode_to_id.get(barcode)
                if not prod_id:
                    continue  # skip if product doesn't exist
                
                conn.execute(
                    text("""INSERT INTO bill_items (bill_id, product_id, quantity, unit_price, subtotal)
                            VALUES (:bill_id, :product_id, :qty, :price, :subtotal)"""),
                    {
                        "bill_id": bill_id,
                        "product_id": prod_id,
                        "qty": qty,
                        "price": price,
                        "subtotal": subtotal
                    }
                )
                item_count += 1
        conn.commit()
        print(f"Seeded {item_count} bill items.")

        # 6. Seed shelves
        print("\nSeeding shelves table from CSV...")
        shelves_path = "smart_retail_500_product_dataset_nagpur/shelves_planogram.csv"
        shelf_count = 0
        shelf_number_to_id = {}
        
        with open(shelves_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                shelf_num = row["shelf_id"].strip()
                floor = int(row["floor_number"])
                aisle = row["aisle"].strip()
                rack = row["rack"].strip()
                category = row["category_zone"].strip()
                
                res = conn.execute(
                    text("""INSERT INTO shelves (floor_number, aisle, rack, shelf_number, category)
                            VALUES (:floor, :aisle, :rack, :shelf_num, :category) RETURNING id"""),
                    {"floor": floor, "aisle": aisle, "rack": rack, "shelf_num": shelf_num, "category": category}
                )
                shelf_db_id = res.scalar()
                shelf_number_to_id[shelf_num] = shelf_db_id
                shelf_count += 1
        conn.commit()
        print(f"Seeded {shelf_count} shelves.")

        # 7. Seed inventory mappings
        print("\nSeeding inventory_mappings from planogram CSV...")
        planogram_path = "smart_retail_500_product_dataset_nagpur/products_500_planogram.csv"
        mapping_count = 0
        
        with open(planogram_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                barcode = row["barcode"].strip()
                shelf_num = row["shelf_id"].strip()
                capacity = int(row["shelf_capacity_units"])
                shelf_qty = int(row["current_shelf_quantity"])
                wh_qty = int(row["warehouse_quantity"])
                min_qty = int(row["minimum_shelf_quantity"])
                
                prod_id = barcode_to_id.get(barcode)
                shelf_db_id = shelf_number_to_id.get(shelf_num)
                
                if not prod_id or not shelf_db_id:
                    continue
                
                # Check duplicate mappings
                res = conn.execute(
                    text("SELECT EXISTS(SELECT 1 FROM inventory_mappings WHERE product_id = :prod_id);"),
                    {"prod_id": prod_id}
                )
                if res.scalar():
                    continue

                conn.execute(
                    text("""INSERT INTO inventory_mappings (product_id, shelf_id, shelf_capacity, current_shelf_quantity, warehouse_quantity, minimum_shelf_quantity, last_refilled_at)
                            VALUES (:prod_id, :shelf_db_id, :capacity, :shelf_qty, :wh_qty, :min_qty, NULL)"""),
                    {
                        "prod_id": prod_id,
                        "shelf_db_id": shelf_db_id,
                        "capacity": capacity,
                        "shelf_qty": shelf_qty,
                        "wh_qty": wh_qty,
                        "min_qty": min_qty
                    }
                )
                
                # Parse additional analytics fields
                movement_class = row["movement_class"].strip() if row.get("movement_class") else None
                cost_price_val = Decimal(row["cost_price"].strip()) if row.get("cost_price") else None
                max_stock_val = int(row["max_stock_capacity"].strip()) if row.get("max_stock_capacity") else None
                
                expiry_date_val = None
                if row.get("expiry_date"):
                    exp_str = row["expiry_date"].strip()
                    if exp_str and exp_str.lower() != "null":
                        try:
                            expiry_date_val = datetime.strptime(exp_str, "%Y-%m-%d").date()
                        except:
                            try:
                                expiry_date_val = datetime.strptime(exp_str, "%d-%m-%Y").date()
                            except:
                                expiry_date_val = None

                # Align products.quantity = shelf_qty + wh_qty and update metadata
                conn.execute(
                    text("""UPDATE products 
                            SET quantity = :qty, 
                                movement_class = :movement_class, 
                                expiry_date = :expiry_date, 
                                cost_price = :cost_price, 
                                max_stock_capacity = :max_stock_capacity 
                            WHERE id = :prod_id;"""),
                    {
                        "qty": shelf_qty + wh_qty,
                        "movement_class": movement_class,
                        "expiry_date": expiry_date_val,
                        "cost_price": cost_price_val,
                        "max_stock_capacity": max_stock_val,
                        "prod_id": prod_id
                    }
                )
                
                mapping_count += 1
        conn.commit()
        print(f"Seeded {mapping_count} inventory mappings.")

        # 8. Reset autoincrement sequences
        print("\nResetting database sequences...")
        sequence_resets = [
            "SELECT setval('products_id_seq', COALESCE((SELECT MAX(id) FROM products), 1));",
            "SELECT setval('customers_id_seq', COALESCE((SELECT MAX(id) FROM customers), 1));",
            "SELECT setval('bills_id_seq', COALESCE((SELECT MAX(id) FROM bills), 1));",
            "SELECT setval('shelves_id_seq', COALESCE((SELECT MAX(id) FROM shelves), 1));",
            "SELECT setval('inventory_mappings_id_seq', COALESCE((SELECT MAX(id) FROM inventory_mappings), 1));",
            "SELECT setval('refill_logs_id_seq', COALESCE((SELECT MAX(id) FROM refill_logs), 1));",
        ]
        for query in sequence_resets:
            try:
                conn.execute(text(query))
            except Exception as e:
                print(f"  [Skip/Error] Resetting sequence: {e}")
        conn.commit()

    print("\nDatabase Seeding Done Successfully!")

if __name__ == "__main__":
    run_seed()
