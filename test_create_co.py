
from unittest.mock import patch, MagicMock
from main import create_customer_order, list_customer_orders
from models import get_engine, get_session, Customer, Product, CustomerOrder

def test_create_co_flow():
    engine = get_engine()
    session = get_session(engine)
    
    # 1. Setup Data
    # Customer
    c = session.query(Customer).filter_by(customer_name="Test CO Customer").first()
    if not c:
        c = Customer(
            customer_name="Test CO Customer",
            ship_to_addr1="123 Test St",
            ship_to_city="Test City",
            ship_to_state="TS",
            ship_to_zip="12345",
            ship_to_country="TestLand",
            bill_to_addr1="123 Bill St",
            bill_to_city="Bill City",
            bill_to_state="BS",
            bill_to_zip="54321",
            bill_to_country="BillLand"
        )
        session.add(c)
    
    # Product
    p = session.query(Product).filter_by(sku="TEST-SKU-CO").first()
    if not p:
        p = Product(sku="TEST-SKU-CO", name="Test Product CO", unit_price="10.0")
        session.add(p)
        
    session.commit()
    c_id = c.id
    p_id = p.id
    
    print(f"Test Customer ID: {c_id}, Product ID: {p_id}")

    # 2. Mocking
    
    # Inputs for create_customer_order:
    # pick_customer is called first. I'll mock that separately.
    # Inside function:
    # safe_input("Invoice Number..."): "INV-TEST-001"
    # safe_input("PO Number..."): "PO-TEST-100"
    # safe_input("Date..."): "" (Use today)
    # safe_input("Tracking..."): "TRACK123"
    # safe_input("Notes..."): "Test Note"
    # safe_input("Use Default? (Bill To)..."): "y"
    # safe_input("Use Default? (Ship To)..."): "n"
    # safe_input("Enter Ship To..."): "Override Ship Address"
    # safe_input("Enter Ship To..."): "" (finish address)
    # Loop Line Items:
    # prompt("Select Product..."): "TEST-SKU-CO - Test Product CO" (Mock prompt)
    # safe_input("Quantity..."): "5"
    # safe_input("Unit..."): "EA"
    # safe_input("Unit Price..."): "" (Keep default)
    # safe_input("Description..."): "" (Keep default)
    # Loop Line Items again:
    # prompt("Select Product..."): "" (Finish)
    # safe_input("Shipping Cost..."): "50.0"
    # safe_input("Discount..."): "10.0"
    # safe_input("Amount Paid..."): "0.0"
    # safe_input("Credit Applied..."): "0.0"
    
    inputs = [
        "INV-TEST-001",
        "PO-TEST-100",
        "", # Date
        "TRACK123",
        "Test Note",
        "y", # Bill Default
        "n", # Ship Default
        "Override Ship Address",
        "",
        # Line Item 1
        "5", # Qty
        "EA", # Unit
        "", # Price
        "", # Desc
        # Financials
        "50.0",
        "10.0",
        "0.0",
        "0.0"
    ]
    input_gen = (i for i in inputs)
    
    def mock_safe_input(prompt_text):
        try:
            val = next(input_gen)
            # print(f"Mock Input [{prompt_text}]: {val}")
            return val
        except StopIteration:
            return ""

    def mock_prompt(text, completer=None):
        # We need to return valid product selection string
        # The logic in main calls prompt("Select Product...").
        # If we return the product key, it works.
        # But we need to handle "Select Product" vs others if any.
        # Logic: First call = product, Second call = empty (to end loop)
        
        # Using a mutable counter or checking caller stack is hard.
        # simpler: create a generator for prompt too.
        pass
        
    prompt_vals = [
        f"TEST-SKU-CO - Test Product CO | ID: {p_id}", # Does logic use ID in string?
        # Checked code: prod_map = {f"{p.sku} - {p.name}": p ...}
        # It does NOT verify ID in string for Customer Order creation, just exact map key.
        # Wait, lines 1060: prod_map = {f"{p.sku} - {p.name}": p for p in products}
        # So I must match that format.
        f"TEST-SKU-CO - Test Product CO",
        ""
    ]
    prompt_gen = (p for p in prompt_vals)
    
    def mock_prompt_func(text, completer=None):
        try:
            val = next(prompt_gen)
            # print(f"Mock Prompt [{text}]: {val}")
            return val
        except StopIteration:
            return ""

    # Mock pick_customer
    def mock_pick_customer(session):
        return c

    with patch('main.safe_input', side_effect=mock_safe_input), \
         patch('main.prompt', side_effect=mock_prompt_func), \
         patch('main.pick_customer', side_effect=mock_pick_customer):
         
         print("Running create_customer_order...")
         create_customer_order(session)

    # Verify Logic
    co = session.query(CustomerOrder).filter_by(invoice_number="INV-TEST-001").first()
    if co:
        print(f"SUCCESS: Customer Order created. ID: {co.id}")
        print(f"Total Lines: {len(co.lines)}")
        print(f"Ship To: {co.ship_to_address}")
        
        if co.ship_to_address == "Override Ship Address":
            print("Address Override Verified.")
        else:
            print(f"Address Override Failed. Got: {co.ship_to_address}")
            
        # Clean up
        session.delete(co)
        # Verify deletion cascades to lines?
        # In models.py: lines = relationship(..., cascade="all, delete-orphan")
        session.commit()
        print("Cleanup complete.")
    else:
        print("FAILURE: Customer Order not found.")

if __name__ == "__main__":
    test_create_co_flow()
