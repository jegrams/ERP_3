from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product, ProductLot, Supplier
from datetime import datetime, timedelta

# Setup
db_url = "sqlite:///./app.db"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

def verify_product_lots():
    print("--- Verifying Product and Lot Tracking ---")

    # 1. Create a Supplier (needed for product)
    supplier = Supplier(name="Tech Supplies Inc.", email="sales@techsupplies.com")
    session.add(supplier)
    session.commit()
    print(f"Created Supplier: {supplier.name}")

    # 2. Create a Product with new fields
    product = Product(
        sku="WIDGET-001",
        sku_number="SKU-123456",
        name="Premium Widget",
        category="Widgets",
        description="A high-quality widget",
        cost_price=10.50,
        unit_price=20.00,
        reorder_level=50,
        supplier_id=supplier.id
    )
    session.add(product)
    session.commit()
    print(f"Created Product: {product.name} (SKU: {product.sku}, Cost: {product.cost_price})")

    # 3. Create Lots for the Product
    # Lot A: Older, recieved 10 days ago
    lot_a = ProductLot(
        product_id=product.id,
        lot_number="BATCH-2023-A",
        production_date=datetime.utcnow() - timedelta(days=30),
        date_received=datetime.utcnow() - timedelta(days=10),
        expiration_date=datetime.utcnow() + timedelta(days=365),
        quantity=100,
        cost_price=10.50 # Explicit cost
    )
    
    # Lot B: Newer, received today
    lot_b = ProductLot(
        product_id=product.id,
        lot_number="BATCH-2023-B",
        production_date=datetime.utcnow() - timedelta(days=5),
        date_received=datetime.utcnow(),
        expiration_date=datetime.utcnow() + timedelta(days=400),
        quantity=200,
        # cost_price not set, defaults to 0.0 in DB, but app logic should handle defaulting to Product cost
        cost_price=product.cost_price # Simulate app logic defaulting
    )

    session.add_all([lot_a, lot_b])
    session.commit()
    print(f"Created Lots for {product.name}:")
    print(f"  - {lot_a.lot_number}: Qty {lot_a.quantity}, Rec: {lot_a.date_received.date()}")
    print(f"  - {lot_b.lot_number}: Qty {lot_b.quantity}, Rec: {lot_b.date_received.date()}")

    # 4. Verify FIFO logic (Query ordering)
    print("\n--- Testing FIFO Retrieval ---")
    fifo_lots = session.query(ProductLot).filter_by(product_id=product.id).order_by(ProductLot.date_received.asc()).all()
    
    expected_order = ["BATCH-2023-A", "BATCH-2023-B"]
    retrieved_order = [lot.lot_number for lot in fifo_lots]
    
    print(f"Expected Order: {expected_order}")
    print(f"Retrieved Order: {retrieved_order}")
    
    if expected_order == retrieved_order:
        print("SUCCESS: FIFO logic working (ordered by date_received).")
    else:
        print("FAILURE: FIFO logic incorrect.")

    # 5. Verify Total Quantity Calculation
    total_qty = sum(lot.quantity for lot in product.lots)
    print(f"\nTotal Quantity for {product.name}: {total_qty} (Expected: 300)")
    
    if total_qty == 300:
        print("SUCCESS: Lot aggregation working.")
    else:
        print("FAILURE: Lot aggregation incorrect.")

    # Cleanup (Optional)
    # session.delete(lot_a) 
    # session.delete(lot_b)
    # session.delete(product)
    # session.delete(supplier)
    # session.commit()

if __name__ == "__main__":
    verify_product_lots()
