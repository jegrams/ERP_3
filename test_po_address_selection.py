import unittest
from unittest.mock import patch, MagicMock
from main import create_purchase_order, get_formatted_address
from models import get_engine, get_session, Supplier, Customer, OurCompany, Product, PurchaseOrder

class TestAddressSelection(unittest.TestCase):
    def setUp(self):
        self.engine = get_engine()
        self.session = get_session(self.engine)
        
        # Setup Data
        self.supplier = self.session.query(Supplier).filter_by(name="Test Supplier").first()
        if not self.supplier:
            self.supplier = Supplier(name="Test Supplier", contact_name="Sup Contact", email="sup@test.com")
            self.session.add(self.supplier)
            
        self.customer = self.session.query(Customer).filter_by(customer_name="Test Customer").first()
        if not self.customer:
            self.customer = Customer(
                customer_name="Test Customer",
                ship_to_addr1="123 Cust St",
                ship_to_city="Cust City",
                ship_to_country="USA"
            )
            self.session.add(self.customer)
            
        self.company = self.session.query(OurCompany).first()
        if not self.company:
            self.company = OurCompany(
                company_name="Test Company",
                address1="HQ Addr 1",
                city="HQ City",
                country="HQ Country"
            )
            self.session.add(self.company)
            
        self.product = self.session.query(Product).filter_by(sku="TEST-SKU").first()
        if not self.product:
            self.product = Product(sku="TEST-SKU", name="Test Prod", unit_price="10.0", cost_price="5.0")
            self.session.add(self.product)
            
        self.session.commit()

    def test_create_po_address_selection(self):
        print("\n--- Testing PO Creation with Address Selection ---")
        
        # Mock Inputs sequence associated with create_purchase_order
        # 1. Select Supplier (via prompt) -> "Test Supplier"
        # 2. PO Number -> "PO-TEST-ADDR"
        # 3. Date -> "" (Today)
        # 4. Expected -> ""
        # 5. Terms -> ""
        # 6. Currency -> ""
        # 7. Ship To Selection: "O" (Our Company) -> Should auto-fill
        # 8. Ship Method -> "Air"
        # 9. Incoterm -> "FOB"
        # 10. Port -> "Port X"
        # 11. Consignee: "C" (Customer) -> Then prompt for customer -> "Test Customer"
        # 12. Notify: "M" (Manual) -> "Manual Notify"
        # 13. TC Party: "" (Same as Consignee)
        # 14. Notes -> "Test Notes"
        # 15. Product Selection -> "Test Prod" (via prompt)
        # 16. Qty -> "10"
        # 17. Unit -> "pcs"
        # 18. Cost -> ""
        # 19. Desc -> ""
        # 20. Packing -> "Box"
        # 21. Product Selection -> "" (Finish)
        # 22. Ship Cost -> ""
        # 23. Discount -> ""
        # 24. Tax -> ""
        # 25. Save -> "y"
        
        # Inputs for 'safe_input'
        safe_inputs = [
            "PO-TEST-ADDR", "", "", "", "", # Header
            "O", # Ship To Source -> Our Company
            "Air", "FOB", "Port X", # Logistics
            "C", # Consignee Source -> Customer
            "M", # Notify Source -> Manual
            "Manual Notify", # Notification Manual Input
            "", # TC Party
            "Test Notes", # Notes
            "10", "pcs", "", "", "Box", # Line Item
            "", "", "", "y" # Summary
        ]
        
        # Inputs for 'prompt' (Supplier, Customer Selection, Product)
        # Calls: 
        # 1. Supplier Selection
        # 2. Pick Customer (inside select_address_source for Consignee)
        # 3. Product Selection
        # 4. Product Selection (Empty to finish)
        
        # Helper to construct keys
        sup_key = f"{self.supplier.name} | ID: {self.supplier.id}"
        cust_key = f"{self.customer.customer_name} | ID: {self.customer.id}"
        
        prompt_inputs = [
            sup_key,
            cust_key,
            "Test Prod", # Product map key matching logic might be loose or I need key?
                         # Product map: "{p.sku} - {p.name} | ID: {p.id}"
            "" 
        ]
        
        # Product map key needed?
        # create_purchase_order line: prod_map = {f"{p.sku} - {p.name}": p for p in products}
        prod_key = f"{self.product.sku} - {self.product.name}"
        prompt_inputs[2] = prod_key
        
        safe_iter = iter(safe_inputs)
        prompt_iter = iter(prompt_inputs)
        
        def mock_safe_input(p):
            # print(f"Safe Input Prompt: {p}")
            val = next(safe_iter)
            # print(f"  -> {val}")
            return val
            
        def mock_prompt(p, completer=None):
            # print(f"Prompt: {p}")
            val = next(prompt_iter)
            # print(f"  -> {val}")
            return val
            
        with patch('main.safe_input', side_effect=mock_safe_input):
            with patch('main.prompt', side_effect=mock_prompt):
                create_purchase_order(self.session)
                
        # Verify
        po = self.session.query(PurchaseOrder).filter_by(po_number="PO-TEST-ADDR").first()
        self.assertIsNotNone(po)
        
        # Check Ship To (Our Company)
        expected_ship = get_formatted_address(self.company)
        self.assertEqual(po.ship_to_address, expected_ship)
        
        # Check Consignee (Customer)
        expected_consignee = get_formatted_address(self.customer)
        self.assertEqual(po.consignee, expected_consignee)
        
        # Check Notify (Manual)
        self.assertEqual(po.notify_party, "Manual Notify")
        
        print("SUCCESS: PO Created with correct address selections.")
        
        # Cleanup
        self.session.delete(po)
        self.session.commit()

if __name__ == "__main__":
    unittest.main()
