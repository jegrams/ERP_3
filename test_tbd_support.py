from models import get_engine, get_session, Product

def test_tbd_product():
    engine = get_engine()
    session = get_session(engine)
    
    sku = "TEST-TBD-001"
    
    # Clean up if exists
    existing = session.query(Product).filter_by(sku=sku).first()
    if existing:
        session.delete(existing)
        session.commit()
    
    print("Creating product with 'TBD' price...")
    p = Product(
        sku=sku,
        name="Test TBD Product",
        description="A product with uncertain price",
        unit_price="TBD",
        cost_price="TBD"
    )
    
    session.add(p)
    session.commit()
    
    # Verify
    saved_p = session.query(Product).filter_by(sku=sku).first()
    print(f"Retrieved Product: SKU={saved_p.sku}, Price={saved_p.unit_price}, Cost={saved_p.cost_price}")
    
    if saved_p.unit_price == "TBD" and saved_p.cost_price == "TBD":
        print("SUCCESS: Product saved with TBD prices.")
    else:
        print(f"FAILURE: Prices mismatched. Got {saved_p.unit_price}")

    # Cleanup
    session.delete(saved_p)
    session.commit()

if __name__ == "__main__":
    test_tbd_product()
