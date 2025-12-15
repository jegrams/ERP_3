
from unittest.mock import patch, MagicMock
from excel_invoice_generator import generate_invoice
from models import get_engine, get_session, Customer, Product, CustomerOrder, CustomerOrderLine
from datetime import datetime
import os

def test_invoice_gen():
    engine = get_engine()
    session = get_session(engine)
    
    # 1. Setup Data
    c = session.query(Customer).filter_by(customer_name="Inv Gen Customer").first()
    if not c:
        c = Customer(
            customer_name="Inv Gen Customer",
            ship_to_addr1="123 Inv St",
            ship_to_city="Inv City",
            ship_to_state="CA",
            ship_to_zip="90210",
            ship_to_country="USA",
            bill_to_addr1="123 Bill Inv St",
            bill_to_city="Bill Inv City",
            bill_to_state="CA",
            bill_to_zip="90210",
            bill_to_country="USA"
        )
        session.add(c)
        session.commit()
    
    co = session.query(CustomerOrder).filter_by(invoice_number="INV-GEN-TEST-001").first()
    if not co:
        co = CustomerOrder(
            customer_id=c.id,
            invoice_number="INV-GEN-TEST-001",
            po_number="PO-GEN-001",
            date=datetime.utcnow(),
            tracking_terms="FedEx Ground",
            notes="Test Invoice Gen Note",
            bill_to_address="123 Bill Inv St\nInv City",
            ship_to_address="123 Inv St\nInv City",
            shipping=25.0,
            discount=5.0,
            amount_paid=10.0,
            credit=0.0,
            status='Pending'
        )
        session.add(co)
        session.flush()
        
        # Add Lines
        p = session.query(Product).first()
        if not p:
            p = Product(sku="TEST-PROD", name="Test Product")
            session.add(p)
            session.flush()
            
        line1 = CustomerOrderLine(
            product_id=p.id,
            qty=2,
            unit="EA",
            selling_price=50.0,
            description="Test Line Item 1",
            amount=100.0
        )
        line2 = CustomerOrderLine(
            product_id=p.id,
            qty=1,
            unit="EA",
            selling_price=10.0,
            description="Test Line Item 2",
            amount=10.0
        )
        co.lines.append(line1)
        co.lines.append(line2)
        session.commit()
        
    print(f"Testing Invoice Gen for Order ID: {co.id}")
    
    # 2. Run Generation
    generate_invoice(session, co.id)
    
    # 3. Verify Files
    xlsx_name = "Invoice INV-GEN-TEST-001 - Inv Gen Customer.xlsx"
    pdf_name = "Invoice INV-GEN-TEST-001 - Inv Gen Customer.pdf"
    
    xlsx_path = os.path.join(r"c:\Users\jegra\MyPython\ERP_3\erp_documents", xlsx_name)
    pdf_path = os.path.join(r"c:\Users\jegra\MyPython\ERP_3\erp_pdfs", pdf_name)
    
    if os.path.exists(xlsx_path):
        print(f"SUCCESS: Excel file created at {xlsx_path}")
    else:
        print(f"FAILURE: Excel file not found at {xlsx_path}")
        
    # PDF check (might fail if no Excel installed, but we want to see output)
    if os.path.exists(pdf_path):
        print(f"SUCCESS: PDF file created at {pdf_path}")
    else:
        print(f"WARNING: PDF file not found at {pdf_path} (Expected if no local Excel)")
        
    # Cleanup
    # session.delete(co)
    # session.delete(c)
    # session.commit()

if __name__ == "__main__":
    test_invoice_gen()
