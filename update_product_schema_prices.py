import sqlite3
import os

DB_FILE = 'app.db'

def migrate_prices_to_text():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("Migrating products table to use TEXT for prices...")
    
    # 1. Rename existing table
    try:
        cursor.execute("ALTER TABLE products RENAME TO products_old")
    except sqlite3.OperationalError as e:
        print(f"Error renaming table: {e}")
        return

    # 2. Create new table with TEXT prices (based on models.py definition but modified)
    # Note: explicit definition to ensure correct types.
    # original: sku, sku_number, name, description, category, unit_price, cost_price, reorder_level, is_active, supplier_id
    create_sql = """
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        sku VARCHAR(50) NOT NULL UNIQUE,
        sku_number VARCHAR(50) UNIQUE,
        name VARCHAR(255),
        description VARCHAR(255),
        category VARCHAR(100),
        unit_price TEXT,  -- Changed from Float
        cost_price TEXT,  -- Changed from Float
        reorder_level INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        supplier_id INTEGER,
        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
    )
    """
    cursor.execute(create_sql)

    # 3. Copy data
    # We cast prices to string. If NULL, they remain NULL (or None in python).
    # sqlite dynamically types, so old float values might just copy over, but let's be safe.
    cursor.execute("""
        INSERT INTO products (id, sku, sku_number, name, description, category, unit_price, cost_price, reorder_level, is_active, supplier_id)
        SELECT id, sku, sku_number, name, description, category, CAST(unit_price AS TEXT), CAST(cost_price AS TEXT), reorder_level, is_active, supplier_id
        FROM products_old
    """)

    # 4. Verify count
    cursor.execute("SELECT count(*) FROM products_old")
    old_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM products")
    new_count = cursor.fetchone()[0]

    if old_count == new_count:
        print(f"Successfully migrated {new_count} records.")
        cursor.execute("DROP TABLE products_old")
    else:
        print(f"Migration mismatch: {old_count} vs {new_count}. Rolling back (manually required if commit).")
        # In this script we haven't committed yet.
        # But we can't easily undo the CREATE TABLE in sqlite transaction sometimes.
        # We will just not commit.
        conn.close()
        return

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_prices_to_text()
