from models import get_engine, get_session, PurchaseOrder, PurchaseOrderLine, Supplier, Product
from sqlalchemy.exc import IntegrityError
from datetime import datetime

engine = get_engine()
session = get_session(engine)

def verify_constraints():
    print("Verifying PO Constraints...")

    # 1. Setup Data
    supplier = session.query(Supplier).first()
    if not supplier:
        supplier = Supplier(name="Constraint Test Supplier")
        session.add(supplier)
        session.commit()

    po_num = "PO-UNIQUE-TEST-001"
    
    # Clean up previous runs
    existing = session.query(PurchaseOrder).filter_by(po_number=po_num).first()
    if existing:
        session.delete(existing)
        session.commit()

    # 2. Insert First PO
    po1 = PurchaseOrder(supplier_id=supplier.id, po_number=po_num)
    session.add(po1)
    session.commit()
    print(f"Created PO {po_num}")

    # 3. Attempt Duplicate
    print("Attempting to create duplicate PO...")
    po2 = PurchaseOrder(supplier_id=supplier.id, po_number=po_num)
    session.add(po2)
    
    try:
        session.commit()
        print("ERROR: Duplicate PO number was allowed! Constraint failed.")
    except IntegrityError:
        print("SUCCESS: Duplicate PO number prevented by DB constraint.")
        session.rollback()
    except Exception as e:
        print(f"Unexpected error: {e}")
        session.rollback()

    # Cleanup
    session.delete(po1)
    session.commit()
    print("Cleanup complete.")

if __name__ == "__main__":
    verify_constraints()
