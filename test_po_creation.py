from models import get_engine, get_session, PurchaseOrder, PurchaseOrderLine, Supplier, Product
# from my_app.models import PurchaseOrder, PurchaseOrderLine, Supplier, Product
from datetime import datetime

# Setup
engine = get_engine()
session = get_session(engine)

def verify_po_fields():
    print("Verifying Purchase Order Fields...")
    
    # 1. Create dummy Supplier and Product if needed
    supplier = session.query(Supplier).first()
    if not supplier:
        supplier = Supplier(name="Test Supplier")
        session.add(supplier)
        session.commit()
        
    product = session.query(Product).first()
    if not product:
        product = Product(sku="TEST-SKU", name="Test Product", unit_price=10.0)
        session.add(product)
        session.commit()

    # 2. Create Purchase Order with NEW fields
    po = PurchaseOrder(
        supplier_id=supplier.id,
        po_number="PO-TEST-INTL-001",
        status="Draft",
        date=datetime.now(),
        expected_date=datetime.now(),
        currency="USD",
        payment_terms="Net 45",
        discount_amount=50.00,
        ship_to_address="123 Warehouse Way, Dock 4",
        shipping_method="Ocean Freight",
        shipping_cost=1500.00,
        tax_amount=25.00,
        incoterm="CIF",
        port_of_destination="Vancouver, BC",
        # packing_structure="20kg Paper Sacks", # Moved
        consignee="Mana Organics Pvt. Ltd.",
        notify_party="Same as Consignee",
        notes="Urgent shipment"
    )
    
    # 3. Create Line with NEW fields
    line = PurchaseOrderLine(
        product_id=product.id,
        description="Override Description: Organic Tea",
        qty=100,
        unit="kg",
        cost=12.50,
        packing_structure="20kg Paper Sacks", # Added to line
        quantity_received=0
    )
    po.lines.append(line)
    
    session.add(po)
    session.commit()
    
    # 4. Read back and Verify
    saved_po = session.query(PurchaseOrder).filter_by(po_number="PO-TEST-INTL-001").first()
    
    assert saved_po is not None
    assert saved_po.incoterm == "CIF"
    assert saved_po.port_of_destination == "Vancouver, BC"
    # assert saved_po.packing_structure == "20kg Paper Sacks" # Removed from Header
    assert saved_po.consignee == "Mana Organics Pvt. Ltd."
    assert saved_po.lines[0].unit == "kg"
    assert saved_po.lines[0].description == "Override Description: Organic Tea"
    assert saved_po.lines[0].packing_structure == "20kg Paper Sacks" # Added to Line
    
    print("Verification Successful! PO and Lines saved with all new fields.")
    
    # Cleanup
    session.delete(saved_po)
    session.commit()
    print("Cleanup complete.")

if __name__ == "__main__":
    verify_po_fields()
