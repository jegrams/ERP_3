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

    # 1. Update Products Table
    columns_to_add = [
        ('products', 'sku_number', 'VARCHAR'),
        ('products', 'name', 'VARCHAR'),
        ('products', 'category', 'VARCHAR'),
        ('products', 'cost_price', 'FLOAT DEFAULT 0.0'),
        ('products', 'reorder_level', 'INTEGER DEFAULT 0'),
        ('products', 'is_active', 'BOOLEAN DEFAULT 1'),
        ('products', 'supplier_id', 'INTEGER REFERENCES suppliers(id)')
    ]

    print("Updating Products table...")
    for table_name, col_name, col_type in columns_to_add:
        add_column_if_not_exists(cursor, table_name, col_name, col_type)

    # 2. Create Product Lots Table
    print("Creating product_lots table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_lots (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        lot_number VARCHAR(100) NOT NULL,
        expiration_date DATETIME,
        production_date DATETIME,
        date_received DATETIME,
        quantity INTEGER DEFAULT 0,
        cost_price FLOAT DEFAULT 0.0,
        created_at DATETIME,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    main()
