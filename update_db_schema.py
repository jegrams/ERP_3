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
        # Customer fields (already added, keeping for safety)
        ('customers', 'bill_to_addr1', 'VARCHAR'),
        ('customers', 'bill_to_addr2', 'VARCHAR'),
        ('customers', 'bill_to_city', 'VARCHAR'),
        ('customers', 'bill_to_state', 'VARCHAR'),
        ('customers', 'bill_to_zip', 'VARCHAR'),
        ('customers', 'bill_to_country', 'VARCHAR'),
        ('customers', 'billing_email', 'VARCHAR'),
        ('customers', 'billing_email_name', 'VARCHAR'),
        # New Supplier fields
        ('suppliers', 'contact_name', 'VARCHAR'),
        ('suppliers', 'email', 'VARCHAR'),
        ('suppliers', 'phone', 'VARCHAR'),
        ('suppliers', 'address1', 'VARCHAR'),
        ('suppliers', 'address2', 'VARCHAR'),
        ('suppliers', 'city', 'VARCHAR'),
        ('suppliers', 'state', 'VARCHAR'),
        ('suppliers', 'zip_code', 'VARCHAR'),
        ('suppliers', 'country', 'VARCHAR'),
        # New PurchaseOrder fields
        ('purchase_orders', 'status', 'VARCHAR DEFAULT "Draft"'), # Enums are stored as VARCHAR in SQLite usually
        ('purchase_orders', 'expected_date', 'DATETIME'),
        ('purchase_orders', 'payment_terms', 'VARCHAR'),
        ('purchase_orders', 'shipping_method', 'VARCHAR'),
        ('purchase_orders', 'shipping_cost', 'FLOAT DEFAULT 0.0'),
        ('purchase_orders', 'tax_amount', 'FLOAT DEFAULT 0.0'),
        ('purchase_orders', 'notes', 'VARCHAR'),
        # New OurCompany fields
        ('our_company', 'IRS_Emp_ID', 'VARCHAR'),
        ('our_company', 'CA_Sec_ID', 'VARCHAR'),
        ('our_company', 'BOE_sales_lic_num', 'VARCHAR')
    ]

    print("Updating schema...")
    print("Updating schema...")
    for table_name, col_name, col_type in columns_to_add:
        add_column_if_not_exists(cursor, table_name, col_name, col_type)

    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    main()
