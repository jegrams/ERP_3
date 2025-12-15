
from sqlalchemy import create_engine, text
from models import DATABASE_URL

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Migrating customer_orders...")
        # CustomerOrder columns
        columns_to_add = [
            ("invoice_number", "VARCHAR(50)"),
            ("po_number", "VARCHAR(50)"),
            ("credit", "FLOAT DEFAULT 0.0"),
            ("discount", "FLOAT DEFAULT 0.0"),
            ("amount_paid", "FLOAT DEFAULT 0.0"),
            ("shipping", "FLOAT DEFAULT 0.0"),
            ("tracking_terms", "VARCHAR(100)"),
            ("bill_to_address", "TEXT"),
            ("ship_to_address", "TEXT"),
            ("notes", "TEXT")
        ]
        
        for col, dtype in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE customer_orders ADD COLUMN {col} {dtype}"))
                print(f"Added {col} to customer_orders")
            except Exception as e:
                print(f"Skipping {col} (probably exists): {e}")

        print("Migrating customer_order_lines...")
        # CustomerOrderLine columns
        line_cols = [
            ("description", "VARCHAR(255)"),
            ("unit", "VARCHAR(50)"),
            ("amount", "FLOAT DEFAULT 0.0")
        ]
        
        for col, dtype in line_cols:
            try:
                conn.execute(text(f"ALTER TABLE customer_order_lines ADD COLUMN {col} {dtype}"))
                print(f"Added {col} to customer_order_lines")
            except Exception as e:
                print(f"Skipping {col} (probably exists): {e}")
        
        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
