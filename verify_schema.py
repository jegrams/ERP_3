import sqlite3
from models import get_engine, get_session, Customer
from sqlalchemy import inspect

DB_FILE = 'app.db'

def verify_schema_columns():
    print("Verifying schema columns...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()

    expected_columns = [
        'bill_to_addr1', 'bill_to_addr2', 'bill_to_city', 
        'bill_to_state', 'bill_to_zip', 'bill_to_country', 
        'billing_email', 'billing_email_name'
    ]

    missing = []
    for col in expected_columns:
        if col in columns:
            print(f"  [OK] Column '{col}' exists.")
        else:
            print(f"  [FAIL] Column '{col}' matches.")
            missing.append(col)
    
    if missing:
        print(f"FAILED: Missing columns: {missing}")
        exit(1)
    else:
        print("Schema verification passed.")

def verify_orm_interaction():
    print("\nVerifying ORM interaction...")
    engine = get_engine()
    session = get_session(engine)

    try:
        # Fetch first customer just to check mapping
        customer = session.query(Customer).first()
        if customer:
            print(f"  Fetched customer: {customer.customer_name}")
            # Try setting a billing field (in memory only, or rollback)
            customer.bill_to_city = "Test City"
            print("  Successfully set bill_to_city on customer object.")
        else:
            print("  No customers found to test, but query executed successfully.")
        
        print("ORM verification passed.")
    except Exception as e:
        print(f"ORM verification FAILED: {e}")
        exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    verify_schema_columns()
    verify_orm_interaction()
