from models import get_engine, get_session, PurchaseOrder, OurCompany
from po_pdf_generator import generate_po_pdf
import os

def test_pdf():
    engine = get_engine()
    session = get_session(engine)
    
    # Get last PO
    po = session.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).first()
    if not po:
        print("No POs found to test.")
        return
        
    our_company = session.query(OurCompany).first()
    
    print(f"Generating PDF for PO {po.po_number}...")
    filepath = generate_po_pdf(po, our_company)
    
    if os.path.exists(filepath):
        print(f"SUCCESS: PDF created at {filepath}")
    else:
        print("ERROR: PDF file not found.")

if __name__ == "__main__":
    test_pdf()
