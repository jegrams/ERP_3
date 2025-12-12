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
        # PurchaseOrder New Field v3
        ('purchase_orders', 'tc_party', 'TEXT')
    ]

    print("Updating schema v3 (TC Party)...")
    for table_name, col_name, col_type in columns_to_add:
        add_column_if_not_exists(cursor, table_name, col_name, col_type)

    conn.commit()
    conn.close()
    print("Schema update v3 complete.")

if __name__ == "__main__":
    main()
