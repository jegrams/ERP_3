from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

# --- Contact Models ---
class Supplier(Base):
    __tablename__ = 'suppliers'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address1 = Column(String(255), nullable=True)
    address2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    # New fields
    tax_id = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    bill_to_addr1 = Column(String(255), nullable=True)
    bill_to_addr2 = Column(String(255), nullable=True)
    bill_to_city = Column(String(100), nullable=True)
    bill_to_state = Column(String(100), nullable=True)
    bill_to_zip = Column(String(20), nullable=True)
    bill_to_country = Column(String(100), nullable=True)
    # contact_info removed as requested
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}')>"

class OurCompany(Base):
    __tablename__ = 'our_company'
    id = Column(Integer, primary_key=True)
    company_name = Column(String(255), nullable=False)
    address1 = Column(String(255), nullable=True)
    address2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    IRS_Emp_ID = Column(String(50), nullable=True)
    CA_Sec_ID = Column(String(50), nullable=True)
    BOE_sales_lic_num = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<OurCompany(name='{self.company_name}')>"

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    contact_name = Column(String, nullable=True)
    ship_to_phone = Column(String, nullable=True)
    email_address = Column(String, unique=True, nullable=True)
    ship_to_addr1 = Column(String, nullable=True)
    ship_to_addr2 = Column(String, nullable=True)
    ship_to_city = Column(String, nullable=True)
    ship_to_state = Column(String, nullable=True)
    ship_to_zip = Column(String, nullable=True)
    ship_to_country = Column(String, nullable=True)
    email_name = Column(String, nullable=True)
    bill_to_addr1 = Column(String, nullable=True)
    bill_to_addr2 = Column(String, nullable=True)
    bill_to_city = Column(String, nullable=True)
    bill_to_state = Column(String, nullable=True)
    bill_to_zip = Column(String, nullable=True)
    bill_to_country = Column(String, nullable=True)
    billing_email = Column(String, nullable=True)
    billing_email_name = Column(String, nullable=True)

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.customer_name}')>"

# --- Product Model ---
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False)
    sku_number = Column(String(50), unique=True, nullable=True) # Distinct from sku if needed
    name = Column(String(255), nullable=True) # Short display name
    description = Column(String(255))
    category = Column(String(100), nullable=True)
    unit_price = Column(String(50), default="0.0") # Changed to String for TBD support
    cost_price = Column(String(50), default="0.0") # Changed to String for TBD support
    reorder_level = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)

    supplier = relationship("Supplier")
    lots = relationship("ProductLot", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(sku='{self.sku}', name='{self.name}')>"

class ProductLot(Base):
    __tablename__ = 'product_lots'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    lot_number = Column(String(100), nullable=False)
    expiration_date = Column(DateTime, nullable=True)
    production_date = Column(DateTime, nullable=True)
    date_received = Column(DateTime, default=datetime.utcnow)
    quantity = Column(Integer, default=0)
    cost_price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="lots")

    def __repr__(self):
        return f"<ProductLot(lot='{self.lot_number}', qty={self.quantity})>"

# --- Order Models ---
class PurchaseOrder(Base):
    __tablename__ = 'purchase_orders'
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    
    # New Fields
    display_status = Column(String(50), default='Draft') # For UI display if needed, or use Enum
    status = Column(Enum('Draft', 'Sent', 'Accepted', 'Received', 'Cancelled', 'Closed', name='po_status'), default='Draft')
    
    # Standard Fields
    po_number = Column(String(50), unique=True, nullable=True) # e.g. PO-2025-001
    created_by = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    vendor_reference = Column(String(100), nullable=True) # Vendor Quote/Invoice #
    
    # Dates
    expected_date = Column(DateTime, nullable=True)
    
    # Financials
    currency = Column(String(10), default='USD')
    payment_terms = Column(String(100), nullable=True) # e.g. "Net 30"
    discount_amount = Column(Float, default=0.0)
    shipping_cost = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    
    # Shipping & Logistics
    ship_to_address = Column(Text, nullable=True) # Full address override
    shipping_method = Column(String(100), nullable=True) # e.g. DHL, FedEx
    incoterm = Column(String(50), nullable=True) # e.g. CIF, FOB
    port_of_destination = Column(String(100), nullable=True)
    # packing_structure moved to Line Item
    consignee = Column(Text, nullable=True) # For Bill of Lading
    notify_party = Column(Text, nullable=True) # For Bill of Lading
    tc_party = Column(Text, nullable=True) # Transaction/Transfer Party?
    
    notes = Column(Text, nullable=True)

    supplier = relationship("Supplier")
    lines = relationship("PurchaseOrderLine", back_populates="order", cascade="all, delete-orphan")

class PurchaseOrderLine(Base):
    __tablename__ = 'purchase_order_lines'
    id = Column(Integer, primary_key=True)
    po_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Line Details
    description = Column(String(255), nullable=True) # Override product name
    qty = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=True) # e.g. kg, lb, ea
    cost = Column(Float, nullable=False)
    packing_structure = Column(String(255), nullable=True) # e.g. "20kg Paper Sacks"
    
    # Reception Tracking
    quantity_received = Column(Integer, default=0)
    received_date = Column(DateTime, nullable=True)
    
    order = relationship("PurchaseOrder", back_populates="lines")
    product = relationship("Product")

class CustomerOrder(Base):
    __tablename__ = 'customer_orders'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum('Pending', 'Invoiced', 'Cancelled', name='order_status'), default='Pending')
    
    # New Fields for Invoice Generation
    invoice_number = Column(String(50), unique=True, nullable=True)
    po_number = Column(String(50), nullable=True) # Customer's PO
    
    # Financials
    credit = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    amount_paid = Column(Float, default=0.0)
    shipping = Column(Float, default=0.0)
    
    # Logistics & Terms
    tracking_terms = Column(String(100), nullable=True) # e.g. FedEx 12345
    
    # Addresses (Text to allow full snapshot)
    bill_to_address = Column(Text, nullable=True)
    ship_to_address = Column(Text, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    customer = relationship("Customer")
    lines = relationship("CustomerOrderLine", back_populates="order", cascade="all, delete-orphan")

class CustomerOrderLine(Base):
    __tablename__ = 'customer_order_lines'
    id = Column(Integer, primary_key=True)
    co_id = Column(Integer, ForeignKey('customer_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    qty = Column(Integer, nullable=False)
    selling_price = Column(Float, nullable=False)
    
    # Detail fields
    description = Column(String(255), nullable=True) # Override product name
    unit = Column(String(50), nullable=True)
    amount = Column(Float, default=0.0) # qty * selling_price usually, but explicit for exact matching
    
    order = relationship("CustomerOrder", back_populates="lines")
    product = relationship("Product")

# --- Invoice Models ---
class Invoice(Base):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True)
    type = Column(Enum('Proforma', 'Commercial', name='invoice_type'), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    customer_order_id = Column(Integer, ForeignKey('customer_orders.id'), nullable=True) # Optional link
    
    order = relationship("CustomerOrder")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceLine(Base):
    __tablename__ = 'invoice_lines'
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    description = Column(String(255), nullable=False)
    qty = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    
    invoice = relationship("Invoice", back_populates="lines")

# --- Document Model ---
class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    reference_id = Column(Integer, nullable=False) # ID of Order or Invoice
    reference_type = Column(String(50), nullable=False) # 'CustomerOrder', 'Invoice', etc.
    file_path = Column(String(500), nullable=False)
    description = Column(String(255))

# --- Database Initialization ---
# Default connection string (User should change this if needed)
DATABASE_URL = "sqlite:///./app.db"  # file in current folder

def get_engine(db_url=DATABASE_URL):
    return create_engine(db_url, echo=False)

def init_db(engine):
    Base.metadata.create_all(engine)

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
