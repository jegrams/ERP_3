import sqlite3
import os

DB_FILE = 'app.db'

def add_column_if_not_exists(cursor, table, column, col_type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"Added column {column} to {table}")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print(f"Column {column} already exists in {table}")
        else:
            raise e

def main():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    columns_to_add = [
        # PurchaseOrder New Fields
        ('purchase_orders', 'po_number', 'VARCHAR(50)'),
        ('purchase_orders', 'created_by', 'VARCHAR(100)'),
        ('purchase_orders', 'approved_by', 'VARCHAR(100)'),
        ('purchase_orders', 'vendor_reference', 'VARCHAR(100)'),
        ('purchase_orders', 'currency', 'VARCHAR(10) DEFAULT "USD"'),
        ('purchase_orders', 'discount_amount', 'FLOAT DEFAULT 0.0'),
        ('purchase_orders', 'ship_to_address', 'TEXT'),
        ('purchase_orders', 'incoterm', 'VARCHAR(50)'),
        ('purchase_orders', 'port_of_destination', 'VARCHAR(100)'),
        ('purchase_orders', 'packing_structure', 'VARCHAR(255)'),
        ('purchase_orders', 'consignee', 'TEXT'),
        ('purchase_orders', 'notify_party', 'TEXT'),
        
        # PurchaseOrderLine New Fields
        ('purchase_order_lines', 'description', 'VARCHAR(255)'),
        ('purchase_order_lines', 'unit', 'VARCHAR(50)'),
        ('purchase_order_lines', 'quantity_received', 'INTEGER DEFAULT 0'),
        ('purchase_order_lines', 'received_date', 'DATETIME')
    ]

    print("Updating schema for Purchase Orders...")
    for table_name, col_name, col_type in columns_to_add:
        add_column_if_not_exists(cursor, table_name, col_name, col_type)

    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    main()
