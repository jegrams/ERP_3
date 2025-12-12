from unittest.mock import patch
from main import edit_customer
from models import get_engine, get_session, Customer

def test_edit_customer_ui():
    engine = get_engine()
    session = get_session(engine)
    
    # 1. Setup - Create or Get Customer
    c = session.query(Customer).filter_by(customer_name="Test Edit Customer").first()
    if not c:
        c = Customer(
            customer_name="Test Edit Customer",
            contact_name="Original Contact",
            email_address="original@test.com",
            ship_to_phone="555-0000",
            ship_to_addr1="123 Old St",
            ship_to_city="Old City",
            ship_to_state="CA",
            ship_to_zip="90000",
            ship_to_country="USA"
        )
        session.add(c)
        session.commit()
        print("Created Test Customer.")
    
    c_id = c.id
    print(f"Testing Edit on Customer ID: {c_id}")

    # 2. Mock Inputs
    # Order: Name, Contact, Email, Phone, Addr1, Addr2, City, State, Zip, Country,
    #        BillAddr1, BillAddr2, BillCity, BillState, BillZip, BillCountry, BillEmail
    # Action: Change Contact, Keep Email, Change Phone, Keep Addr, Set BillAddr1
    inputs = [
        "",                 # Name (Keep)
        "New Contact",      # Contact (Change)
        "",                 # Email (Keep)
        "555-9999",         # Phone (Change)
        "", "", "", "", "", "", # Address (Keep all)
        "999 Bill St",      # Bill Addr 1 (Change)
        "", "New York", "NY", "10001", "USA", "billing@test.com" # Billing Info
    ]
    
    input_gen = (i for i in inputs)
    
    def mock_input(prompt):
        try:
            val = next(input_gen)
            # print(f"Mock Input: {val}")
            return val
        except StopIteration:
            return ""

    # 3. patch main.safe_input
    with patch('main.safe_input', side_effect=mock_input):
        edit_customer(session, c)
        
    # 4. Verify
    session.refresh(c)
    
    success = True
    if c.contact_name != "New Contact":
        print(f"FAILURE: Contact Name not updated. Got '{c.contact_name}'")
        success = False
    
    if c.ship_to_phone != "555-9999":
        print(f"FAILURE: Phone not updated. Got '{c.ship_to_phone}'")
        success = False
        
    if c.email_address != "original@test.com":
        print(f"FAILURE: Email changed unexpectedly. Got '{c.email_address}'")
        success = False

    if success:
        print("SUCCESS: Customer updated correctly via UI.")
        
    # Cleanup
    session.delete(c)
    session.commit()

if __name__ == "__main__":
    test_edit_customer_ui()
