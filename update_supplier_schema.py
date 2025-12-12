import sqlite3
import os

DB_FILE = 'app.db'

def main():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Add new columns
    new_columns = [
        ('tax_id', 'VARCHAR(50)'),
        ('notes', 'TEXT'),
        ('bill_to_addr1', 'VARCHAR(255)'),
        ('bill_to_addr2', 'VARCHAR(255)'),
        ('bill_to_city', 'VARCHAR(100)'),
        ('bill_to_state', 'VARCHAR(100)'),
        ('bill_to_zip', 'VARCHAR(20)'),
        ('bill_to_country', 'VARCHAR(100)')
    ]

    print("Adding new columns to Valid Suppliers...")
    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE suppliers ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print(f"Column {col_name} already exists")
            else:
                print(f"Error adding {col_name}: {e}")

    # Drop contact_info column
    # SQLite 3.35.0+ supports DROP COLUMN. If this fails, we might need a fallback, but let's try direct drop first.
    print("Dropping contact_info column...")
    try:
        cursor.execute("ALTER TABLE suppliers DROP COLUMN contact_info")
        print("Dropped column contact_info")
    except sqlite3.OperationalError as e:
        print(f"Error dropping contact_info (might not be supported in this SQLite version or column missing): {e}")

    conn.commit()
    conn.close()
    print("Supplier schema update complete.")

if __name__ == "__main__":
    main()
