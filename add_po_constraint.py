import sqlite3
import os

DB_FILE = 'app.db'

def main():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("Adding unique constraint (index) to po_number...")
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_purchase_orders_po_number ON purchase_orders(po_number)")
        print("Unique index created successfully.")
    except sqlite3.Error as e:
        print(f"Error creating index: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
