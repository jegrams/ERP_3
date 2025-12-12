from unittest.mock import patch
from main import edit_purchase_order, safe_input
from models import get_engine, get_session, PurchaseOrder, Supplier

def test_edit_ui():
    engine = get_engine()
    session = get_session(engine)
    
    # Setup: Get or create a PO
    po = session.query(PurchaseOrder).first()
    if not po:
        print("No PO found to test.")
        return

    original_status = po.status
    original_terms = po.payment_terms
    
    print(f"Original Status: {original_status}")
    print(f"Original Terms: {original_terms}")
    
    # Inputs sequence:
    # 1. New Status -> "Sent"
    # 2. Date -> "" (Keep)
    # 3. Terms -> "Net 30" (Change)
    # 4. Ship Via -> "" (Keep)
    # 5. Ship To -> ""
    # 6. Incoterm -> ""
    # 7. Port -> ""
    # 8. Consignee -> ""
    # 9. Notify -> ""
    # 10. TC Party -> ""
    # 11. Shipping Cost -> ""
    # 12. Discount -> ""
    # 13. Tax -> ""
    # 14. Notes -> "Edited via Test"
    
    inputs = [
        "Sent", 
        "", 
        "Net 30", 
        "", "", "", "", "", "", "", 
        "", "", "", 
        "Edited via Test"
    ]
    
    input_generator = (i for i in inputs)
    
    def mock_input(prompt):
        try:
            val = next(input_generator)
            print(f"Mock Input for '{prompt}': {val}")
            return val
        except StopIteration:
            return ""

    # Patch safe_input in main module? 
    # Since we imported edit_purchase_order from main, it uses main.safe_input.
    # We need to patch main.safe_input.
    
    with patch('main.safe_input', side_effect=mock_input):
        edit_purchase_order(session, po)
        
    # Verify
    session.refresh(po)
    print(f"\nNew Status: {po.status}")
    print(f"New Terms: {po.payment_terms}")
    print(f"New Notes: {po.notes}")
    
    if po.status == "Sent" and po.payment_terms == "Net 30" and po.notes == "Edited via Test":
        print("SUCCESS: PO updated via UI.")
        
        # Revert
        po.status = original_status
        po.payment_terms = original_terms
        session.commit()
    else:
        print("FAILURE: PO not updated correctly.")

if __name__ == "__main__":
    test_edit_ui()
