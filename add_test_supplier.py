import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Supplier, Base

# Setup database connection
DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def add_test_supplier():
    new_supplier = Supplier(
        name="Test Supplier Inc.",
        contact_name="John Doe",
        email="john@testsupplier.com",
        phone="555-0199",
        address1="123 Supplier Lane",
        city="Supply City",
        state="SC",
        zip_code="90210",
        country="USA",
        tax_id="TX-987654321",
        notes="This is a test supplier with a very long note to test the Text column capability. " * 5,
        bill_to_addr1="456 Billing Blvd",
        bill_to_city="Billtown",
        bill_to_state="CA",
        bill_to_zip="90001",
        bill_to_country="USA"
    )
    
    session.add(new_supplier)
    session.commit()
    print(f"Added supplier: {new_supplier.name} with ID: {new_supplier.id}")
    
    # Verify
    s = session.query(Supplier).filter_by(id=new_supplier.id).first()
    print(f"Verification - Tax ID: {s.tax_id}")
    print(f"Verification - Notes length: {len(s.notes)}")
    print(f"Verification - Billing City: {s.bill_to_city}")

if __name__ == "__main__":
    add_test_supplier()
