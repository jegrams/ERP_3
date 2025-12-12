import pandas as pd
import math
from models import get_engine, get_session, Customer
from sqlalchemy.exc import IntegrityError

def import_customers():
    # File path
    file_path = r"C:\Users\jegra\MyPython\ERP_3\my_app\archive\existing_customer_details_11292025.xlsx"
    
    print(f"Reading file: {file_path}")
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Failed to read file: {e}")
        return

    # Database setup
    engine = get_engine()
    session = get_session(engine)
    
    added_count = 0
    skipped_count = 0
    
    print("Starting import...")
    
    try:
        # Pre-fetch existing names and emails to reduce DB queries and handle in-session duplicates
        existing_customers = session.query(Customer.customer_name, Customer.email_address).all()
        existing_names = {c.customer_name for c in existing_customers}
        existing_emails = {c.email_address for c in existing_customers if c.email_address}
        
        for index, row in df.iterrows():
            def clean_val(val):
                if pd.isna(val):
                    return None
                s = str(val).strip()
                return s if s else None

            customer_name = clean_val(row['CustomerName'])
            email_address = clean_val(row['EmailAddress'])
            
            if not customer_name:
                print(f"Skipping row {index}: Missing customer name")
                continue

            # Check for duplicates
            if customer_name in existing_names:
                print(f"Skipping existing customer name: {customer_name}")
                skipped_count += 1
                continue
            
            if email_address and email_address in existing_emails:
                print(f"Skipping existing email address: {email_address} (Customer: {customer_name})")
                skipped_count += 1
                continue

            # Create new Customer object
            new_customer = Customer(
                customer_name=customer_name,
                contact_name=clean_val(row['ContactName']),
                ship_to_phone=clean_val(row['ShipToPhone']),
                email_address=email_address,
                ship_to_addr1=clean_val(row['ShipToAddr1']),
                ship_to_addr2=clean_val(row['ShipToAddr2']),
                ship_to_city=clean_val(row['ShipToCity']),
                ship_to_state=clean_val(row['ShipToState']),
                ship_to_zip=clean_val(row['ShipToZip']),
                ship_to_country=clean_val(row['ShipToCountry']),
                email_name=clean_val(row['EmailName'])
            )
            
            session.add(new_customer)
            
            # Update local sets so we don't add duplicates from the file itself
            existing_names.add(customer_name)
            if email_address:
                existing_emails.add(email_address)
            
            added_count += 1
        
        session.commit()
        print("\nImport completed successfully.")
        print(f"Added: {added_count}")
        print(f"Skipped: {skipped_count}")
        
    except IntegrityError as e:
        session.rollback()
        print(f"Database error occurred during commit: {e}")
    except Exception as e:
        session.rollback()
        print(f"An unexpected error occurred: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    import_customers()
