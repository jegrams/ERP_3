import sys
import os
import shutil
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from tabulate import tabulate
import pandas as pd
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import re

from models import (
    get_engine, init_db, get_session,
    Supplier, Customer, Product, ProductLot,
    PurchaseOrder, PurchaseOrderLine,
    CustomerOrder, CustomerOrderLine,
    Invoice, InvoiceLine, Document,
    OurCompany
)
from pdf_generator import generate_invoice_pdf
from po_pdf_generator import generate_po_pdf

# --- Setup & Helpers ---

DOCS_DIR = "./erp_documents/"
PDFS_DIR = "./erp_pdfs/"

def ensure_directories():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(PDFS_DIR, exist_ok=True)

def print_table(data, headers):
    print(tabulate(data, headers=headers, tablefmt="grid"))

def safe_input(prompt_text):
    """Universal input wrapper that checks for exit codes."""
    try:
        val = input(prompt_text)
    except EOFError:
        return ""
        
    if val.strip().lower() in ('exit', 'quit', 'q'):
        print("Exiting program...")
        sys.exit(0)
    return val

# --- Core CRUD ---

def add_supplier(session: Session):
    print("\n--- Add Supplier ---")
    name = safe_input("Name: ")
    contact_name = safe_input("Contact Name: ")
    email = safe_input("Email: ")
    phone = safe_input("Phone: ")
    tax_id = safe_input("Tax ID: ")
    
    print("--- Shipping/Physical Address ---")
    address1 = safe_input("Address Line 1: ")
    address2 = safe_input("Address Line 2: ")
    city = safe_input("City: ")
    state = safe_input("State: ")
    zip_code = safe_input("Zip: ")
    country = safe_input("Country: ")
    
    print("--- Billing Address ---")
    bill_to_addr1 = safe_input("Address Line 1: ")
    bill_to_addr2 = safe_input("Address Line 2: ")
    bill_to_city = safe_input("City: ")
    bill_to_state = safe_input("State: ")
    bill_to_zip = safe_input("Zip: ")
    bill_to_country = safe_input("Country: ")
    
    print("--- Notes ---")
    print("Enter notes (press Enter twice to finish):")
    lines = []
    while True:
        line = safe_input("")
        if not line: break
        lines.append(line)
    notes = "\n".join(lines)
    
    supplier = Supplier(
        name=name,
        contact_name=contact_name,
        email=email,
        phone=phone,
        tax_id=tax_id,
        address1=address1,
        address2=address2,
        city=city,
        state=state,
        zip_code=zip_code,
        country=country,
        bill_to_addr1=bill_to_addr1,
        bill_to_addr2=bill_to_addr2,
        bill_to_city=bill_to_city,
        bill_to_state=bill_to_state,
        bill_to_zip=bill_to_zip,
        bill_to_country=bill_to_country,
        notes=notes
    )
    session.add(supplier)
    session.commit()
    print(f"Supplier '{name}' added successfully.")

def list_suppliers(session: Session):
    suppliers = session.query(Supplier).all()
    # Using contact_name and email for the list view
    data = [[s.id, s.name, s.contact_name, s.email] for s in suppliers]
    print_table(data, ["ID", "Name", "Contact", "Email"])

def add_customer(session: Session):
    print("\n--- Add Customer ---")
    customer_name = safe_input("Customer Name: ")
    contact_name = safe_input("Contact Name: ")
    email_address = safe_input("Email Address: ")
    ship_to_phone = safe_input("Ship To Phone: ")
    
    print("--- Shipping Address ---")
    ship_to_addr1 = safe_input("Address Line 1: ")
    ship_to_addr2 = safe_input("Address Line 2: ")
    ship_to_city = safe_input("City: ")
    ship_to_state = safe_input("State: ")
    ship_to_zip = safe_input("Zip: ")
    ship_to_country = safe_input("Country: ")
    
    customer = Customer(
        customer_name=customer_name,
        contact_name=contact_name,
        email_address=email_address,
        ship_to_phone=ship_to_phone,
        ship_to_addr1=ship_to_addr1,
        ship_to_addr2=ship_to_addr2,
        ship_to_city=ship_to_city,
        ship_to_state=ship_to_state,
        ship_to_zip=ship_to_zip,
        ship_to_country=ship_to_country
    )
    session.add(customer)
    session.commit()
    print("Customer added successfully.")

def list_customers(session: Session):
    customers = session.query(Customer).all()
    # Display subset of info
    data = [[c.id, c.customer_name] for c in customers]
    print_table(data, ["ID", "Customer Name"])

def pick_customer(session: Session):
    """Helper to interactively select a customer and return the object."""
    customers = session.query(Customer).all()
    if not customers:
        print("No customers found.")
        return None
        
    customer_map = {f"{c.customer_name} | ID: {c.id}": c.id for c in customers}
    choices = list(customer_map.keys())
    completer = WordCompleter(choices, ignore_case=True, match_middle=True)
    
    try:
        user_input = prompt("Select Customer: ", completer=completer)
    except KeyboardInterrupt:
        return None
        
    if not user_input: return None
    
    cust_id = None
    if user_input in customer_map:
        cust_id = customer_map[user_input]
    elif user_input.isdigit():
        cust_id = int(user_input)
    else:
        match = re.search(r"\|\s*ID:\s*(\d+)\s*$", user_input)
        if match:
            cust_id = int(match.group(1))
            
    if cust_id:
        return session.get(Customer, cust_id)
    return None

def get_formatted_address(source_obj):
    """Formats address from OurCompany or Customer object."""
    if isinstance(source_obj, OurCompany):
        lines = [source_obj.company_name, source_obj.address1, source_obj.address2, 
                 f"{source_obj.city or ''} {source_obj.state or ''} {source_obj.zip_code or ''}",
                 source_obj.country]
        return "\n".join(filter(None, lines))
    elif isinstance(source_obj, Customer):
        lines = [source_obj.customer_name, source_obj.ship_to_addr1, source_obj.ship_to_addr2,
                 f"{source_obj.ship_to_city or ''} {source_obj.ship_to_state or ''} {source_obj.ship_to_zip or ''}",
                 source_obj.ship_to_country]
        return "\n".join(filter(None, lines))
    return ""

def select_address_source(session: Session, field_name="Address"):
    """
    Prompts user to select address source.
    Returns: (is_manual_override, value_string)
    If manual, returns (True, None) -> Let caller prompt for text.
    If selection made, returns (False, formatted_address_string).
    """
    print(f"Select source for {field_name}:")
    print(" [M]anual Entry (Type it yourself)")
    print(" [O]ur Company Details")
    print(" [C]ustomer Details")
    print(" [S]kip / Keep Current")
    
    choice = safe_input("Choice [M]: ").strip().upper()
    
    if choice == 'O':
        comp = session.query(OurCompany).first()
        if comp:
            return False, get_formatted_address(comp)
        else:
            print("Our Company details not found.")
            return True, None
    elif choice == 'C':
        cust = pick_customer(session)
        if cust:
            return False, get_formatted_address(cust)
        else:
            return True, None
    elif choice == 'S':
        return False, None # Signal to keep/skip
    else:
        return True, None # Manual

def pick_customer(session: Session):
    """Helper to interactively select a customer and return the object."""
    customers = session.query(Customer).all()
    if not customers:
        print("No customers found.")
        return None
        
    customer_map = {f"{c.customer_name} | ID: {c.id}": c.id for c in customers}
    choices = list(customer_map.keys())
    completer = WordCompleter(choices, ignore_case=True, match_middle=True)
    
    try:
        user_input = prompt("Select Customer: ", completer=completer)
    except KeyboardInterrupt:
        return None
        
    if not user_input: return None
    
    cust_id = None
    if user_input in customer_map:
        cust_id = customer_map[user_input]
    elif user_input.isdigit():
        cust_id = int(user_input)
    else:
        match = re.search(r"\|\s*ID:\s*(\d+)\s*$", user_input)
        if match:
            cust_id = int(match.group(1))
            
    if cust_id:
        return session.get(Customer, cust_id)
    return None

def get_formatted_address(source_obj):
    """Formats address from OurCompany or Customer object."""
    if isinstance(source_obj, OurCompany):
        lines = [source_obj.company_name, source_obj.address1, source_obj.address2, 
                 f"{source_obj.city or ''} {source_obj.state or ''} {source_obj.zip_code or ''}",
                 source_obj.country]
        return "\n".join(filter(None, lines))
    elif isinstance(source_obj, Customer):
        lines = [source_obj.customer_name, source_obj.ship_to_addr1, source_obj.ship_to_addr2,
                 f"{source_obj.ship_to_city or ''} {source_obj.ship_to_state or ''} {source_obj.ship_to_zip or ''}",
                 source_obj.ship_to_country]
        return "\n".join(filter(None, lines))
    return ""

def select_address_source(session: Session, field_name="Address"):
    """
    Prompts user to select address source.
    Returns: (is_manual_override, value_string)
    If manual, returns (True, None) -> Let caller prompt for text.
    If selection made, returns (False, formatted_address_string).
    """
    print(f"Select source for {field_name}:")
    print(" [M]anual Entry (Type it yourself)")
    print(" [O]ur Company Details")
    print(" [C]ustomer Details")
    print(" [S]kip / Keep Current")
    
    choice = safe_input("Choice [M]: ").strip().upper()
    
    if choice == 'O':
        comp = session.query(OurCompany).first()
        if comp:
            return False, get_formatted_address(comp)
        else:
            print("Our Company details not found.")
            return True, None
    elif choice == 'C':
        cust = pick_customer(session)
        if cust:
            return False, get_formatted_address(cust)
        else:
            return True, None
    elif choice == 'S':
        return False, None # Signal to keep/skip
    else:
        return True, None # Manual

def view_customer_details(session: Session):
    print("\n--- View Customer Details (Active Search) ---")
    
    c = pick_customer(session)
    if not c:
        return

    print(f"\nID: {c.id}")
    print(f"Customer Name: {c.customer_name}")
    print(f"Contact Name:  {c.contact_name}")
    print(f"Email:         {c.email_address}")
    print(f"Phone:         {c.ship_to_phone}")
    print("--- Shipping Address ---")
    print(f"{c.ship_to_addr1}")
    if c.ship_to_addr2: print(f"{c.ship_to_addr2}")
    print(f"{c.ship_to_city}, {c.ship_to_state} {c.ship_to_zip}")
    print(f"{c.ship_to_country}")
    
    print(f"{c.ship_to_country}")
    
    print("--- Billing Address ---")
    print(f"{c.bill_to_addr1}")
    if c.bill_to_addr2: print(f"{c.bill_to_addr2}")
    print(f"{c.bill_to_city}, {c.bill_to_state} {c.bill_to_zip}")
    print(f"{c.bill_to_country}")
    print(f"Billing Email: {c.billing_email}")
    
    print("\n")
    action = safe_input("Press [Enter] to go back, or 'e' to Edit: ")
    if action.lower() == 'e':
        edit_customer(session, c)

def edit_customer(session: Session, c: Customer):
    print(f"\n--- Edit Customer {c.customer_name} ---")
    print("Press [Enter] to keep current value.")
    
    c.customer_name = safe_input(f"Customer Name [{c.customer_name}]: ") or c.customer_name
    c.contact_name = safe_input(f"Contact Name [{c.contact_name}]: ") or c.contact_name
    c.email_address = safe_input(f"Email [{c.email_address}]: ") or c.email_address
    c.ship_to_phone = safe_input(f"Phone [{c.ship_to_phone}]: ") or c.ship_to_phone
    
    print("--- Shipping Address ---")
    c.ship_to_addr1 = safe_input(f"Addr 1 [{c.ship_to_addr1}]: ") or c.ship_to_addr1
    c.ship_to_addr2 = safe_input(f"Addr 2 [{c.ship_to_addr2}]: ") or c.ship_to_addr2
    c.ship_to_city = safe_input(f"City [{c.ship_to_city}]: ") or c.ship_to_city
    c.ship_to_state = safe_input(f"State [{c.ship_to_state}]: ") or c.ship_to_state
    c.ship_to_zip = safe_input(f"Zip [{c.ship_to_zip}]: ") or c.ship_to_zip
    c.ship_to_zip = safe_input(f"Zip [{c.ship_to_zip}]: ") or c.ship_to_zip
    c.ship_to_country = safe_input(f"Country [{c.ship_to_country}]: ") or c.ship_to_country
    
    print("--- Billing Address ---")
    c.bill_to_addr1 = safe_input(f"Bill Addr 1 [{c.bill_to_addr1}]: ") or c.bill_to_addr1
    c.bill_to_addr2 = safe_input(f"Bill Addr 2 [{c.bill_to_addr2}]: ") or c.bill_to_addr2
    c.bill_to_city = safe_input(f"Bill City [{c.bill_to_city}]: ") or c.bill_to_city
    c.bill_to_state = safe_input(f"Bill State [{c.bill_to_state}]: ") or c.bill_to_state
    c.bill_to_zip = safe_input(f"Bill Zip [{c.bill_to_zip}]: ") or c.bill_to_zip
    c.bill_to_country = safe_input(f"Bill Country [{c.bill_to_country}]: ") or c.bill_to_country
    c.billing_email = safe_input(f"Billing Email [{c.billing_email}]: ") or c.billing_email
    
    try:
        session.commit()
        print("Customer Updated Successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error updating customer: {e}")

def view_product_details(session: Session):
    print("\n--- View Product Details (Active Search) ---")
    
    products = session.query(Product).all()
    if not products:
        print("No products found.")
        return

    # Create choices: "SKU - Name | ID: <id>"
    product_map = {f"{p.sku} - {p.name or 'No Name'} | ID: {p.id}": p.id for p in products}
    choices = list(product_map.keys())
    
    completer = WordCompleter(choices, ignore_case=True, match_middle=True)
    
    print("Start typing SKU or Name... (Press Tab/Arrows to select, Enter to confirm)")
    try:
        user_input = prompt("Product: ", completer=completer)
    except KeyboardInterrupt:
        return

    if not user_input: return

    prod_id = None
    if user_input in product_map:
        prod_id = product_map[user_input]
    elif user_input.isdigit():
        prod_id = int(user_input)
    else:
        match = re.search(r"\|\s*ID:\s*(\d+)\s*$", user_input)
        if match:
            prod_id = int(match.group(1))
        else:
            print("Invalid selection.")
            return

    p = session.get(Product, prod_id)
    if not p:
        print("Product not found.")
        return

    print(f"\nID: {p.id}")
    print(f"SKU: {p.sku}")
    print(f"SKU Number: {p.sku_number}")
    print(f"Name: {p.name}")
    print(f"Category: {p.category}")
    print(f"Description: {p.description}")
    print(f"Unit Price: ${p.unit_price}")
    print(f"Cost Price: ${p.cost_price}")
    print(f"Reorder Level: {p.reorder_level}")
    print(f"Supplier: {p.supplier.name if p.supplier else 'None'}")
    
    # Lot Calculation
    active_lots = [lot for lot in p.lots if lot.quantity > 0]
    total_qty = sum(l.quantity for l in active_lots)
    print(f"Total Qty On Hand: {total_qty}")
    
    if active_lots:
        print("\nActive Lots:")
        lot_data = [[l.lot_number, l.quantity, l.expiration_date, l.date_received, l.cost_price] for l in active_lots]
        print_table(lot_data, ["Lot #", "Qty", "Expires", "Received", "Cost"])
    else:
        print("\nNo active inventory lots.")

def view_supplier_details(session: Session):
    print("\n--- View Supplier Details (Active Search) ---")
    
    suppliers = session.query(Supplier).all()
    if not suppliers:
        print("No suppliers found.")
        return

    supplier_map = {f"{s.name} | ID: {s.id}": s.id for s in suppliers}
    choices = list(supplier_map.keys())
    completer = WordCompleter(choices, ignore_case=True, match_middle=True)

    try:
        user_input = prompt("Supplier: ", completer=completer)
    except KeyboardInterrupt:
        return

    if not user_input: return

    sup_id = None
    if user_input in supplier_map:
        sup_id = supplier_map[user_input]
    elif user_input.isdigit():
        sup_id = int(user_input)
    else:
        match = re.search(r"\|\s*ID:\s*(\d+)\s*$", user_input)
        if match:
            sup_id = int(match.group(1))
        else:
            print("Invalid selection.")
            return

    s = session.get(Supplier, sup_id)
    if not s: return

    print(f"\nID: {s.id}")
    print(f"Name: {s.name}")
    print(f"Contact Name: {s.contact_name}")
    print(f"Tax ID:       {s.tax_id}")
    print(f"Email:        {s.email}")
    print(f"Phone:        {s.phone}")
    
    print("--- Billing Address ---")
    print(f"{s.bill_to_addr1}")
    if s.bill_to_addr2: print(f"{s.bill_to_addr2}")
    print(f"{s.bill_to_city}, {s.bill_to_state} {s.bill_to_zip}")
    print(f"{s.bill_to_country}")

    print("--- Shipping/Physical Address ---")
    print(f"{s.address1}")
    if s.address2: print(f"{s.address2}")
    print(f"{s.city}, {s.state} {s.zip_code}")
    print(f"{s.country}")
    
    print("--- Notes ---")
    print(s.notes)
    
    print("\n")
    while True:
        action = safe_input("Press [Enter] to go back, 'e' to Edit, 'd' to Delete: ").strip().lower()
        if action == 'e':
            edit_supplier(session, s)
            # Re-display details is a bit complex in this simple CLI structure without clearing screen
            # But we can just loop back to view or return. 
            # Let's just return to allow user to re-select or we could recursively call view_supplier... 
            # actually better to just break and let them re-select if they want, 
            # OR simple re-print current obj status.
            print("\n(Updated Details)")
            print(f"Name: {s.name}")
            print(f"Contact: {s.contact_name}")
            # ... simple cheat: just return to menu
            return 
        elif action == 'd':
            if delete_supplier(session, s):
                return # Successfully deleted
            # If not deleted, loop continues
        else:
            return

def edit_supplier(session: Session, s: Supplier):
    print(f"\n--- Edit Supplier {s.name} ---")
    print("Press [Enter] to keep current value.")
    
    s.name = safe_input(f"Name [{s.name}]: ") or s.name
    s.contact_name = safe_input(f"Contact Name [{s.contact_name}]: ") or s.contact_name
    s.email = safe_input(f"Email [{s.email}]: ") or s.email
    s.phone = safe_input(f"Phone [{s.phone}]: ") or s.phone
    s.tax_id = safe_input(f"Tax ID [{s.tax_id}]: ") or s.tax_id
    
    print("--- Shipping/Physical Address ---")
    s.address1 = safe_input(f"Address 1 [{s.address1}]: ") or s.address1
    s.address2 = safe_input(f"Address 2 [{s.address2}]: ") or s.address2
    s.city = safe_input(f"City [{s.city}]: ") or s.city
    s.state = safe_input(f"State [{s.state}]: ") or s.state
    s.zip_code = safe_input(f"Zip [{s.zip_code}]: ") or s.zip_code
    s.country = safe_input(f"Country [{s.country}]: ") or s.country
    
    print("--- Billing Address ---")
    s.bill_to_addr1 = safe_input(f"Bill Addr 1 [{s.bill_to_addr1}]: ") or s.bill_to_addr1
    s.bill_to_addr2 = safe_input(f"Bill Addr 2 [{s.bill_to_addr2}]: ") or s.bill_to_addr2
    s.bill_to_city = safe_input(f"Bill City [{s.bill_to_city}]: ") or s.bill_to_city
    s.bill_to_state = safe_input(f"Bill State [{s.bill_to_state}]: ") or s.bill_to_state
    s.bill_to_zip = safe_input(f"Bill Zip [{s.bill_to_zip}]: ") or s.bill_to_zip
    s.bill_to_country = safe_input(f"Bill Country [{s.bill_to_country}]: ") or s.bill_to_country

    print("--- Notes ---")
    # For notes, it's multiline, simpler to just replace or append? 
    # Let's just ask if they want to overwrite notes
    print(f"Current Notes: {s.notes}")
    change_notes = safe_input("Edit Notes? (y/n) [n]: ").lower()
    if change_notes == 'y':
        print("Enter new notes (press Enter twice to finish):")
        lines = []
        while True:
            line = safe_input("")
            if not line: break
            lines.append(line)
        s.notes = "\n".join(lines)
    
    try:
        session.commit()
        print("Supplier Updated Successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error updating supplier: {e}")

def delete_supplier(session: Session, s: Supplier) -> bool:
    print(f"\n!!! WARNING: Deleting Supplier {s.name} !!!")
    confirm = safe_input("Are you sure? This cannot be undone. (y/n): ")
    if confirm.lower() == 'y':
        try:
            session.delete(s)
            session.commit()
            print(f"Supplier {s.name} deleted.")
            return True
        except Exception as e:
            session.rollback()
            print(f"Error deleting supplier (likely used in POs or Products): {e}")
            return False
    print("Deletion cancelled.")
    return False

def add_product(session: Session):
    print("\n--- Add Product ---")
    sku = safe_input("SKU: ")
    name = safe_input("Name: ")
    desc = safe_input("Description: ")
    
    price = "0.0"
    while True:
        p_in = safe_input("Unit Price [0.0] (or TBD): ")
        if not p_in:
            break # Use default 0.0
        
        # Check if valid float or "TBD"
        try:
            float(p_in)
            price = p_in
            break
        except ValueError:
            if p_in.strip().upper() == "TBD":
                price = "TBD"
                break
            print("Invalid price. Please enter a number or 'TBD'.")
            # Loop continues
    
    product = Product(sku=sku, name=name, description=desc, unit_price=price)
    session.add(product)
    try:
        session.commit()
        print("Product added successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error adding product: {e}")

def list_products(session: Session):
    products = session.query(Product).all()
    data = [[p.id, p.sku, p.name, p.unit_price] for p in products]
    print_table(data, ["ID", "SKU", "Name", "Price"])

# --- Order Management ---

def create_purchase_order(session: Session):
    print("\n--- Create Purchase Order ---")
    
    # 1. Select Supplier
    suppliers = session.query(Supplier).all()
    if not suppliers:
        print("No suppliers found. Please add a supplier first.")
        return
    
    supplier_map = {f"{s.name} | ID: {s.id}": s.id for s in suppliers}
    completer = WordCompleter(list(supplier_map.keys()), ignore_case=True, match_middle=True)
    
    try:
        sup_input = prompt("Select Supplier: ", completer=completer)
    except KeyboardInterrupt: return
    
    if not sup_input: return
    
    supplier_id = None
    if sup_input in supplier_map:
        supplier_id = supplier_map[sup_input]
    elif sup_input.isdigit():
        supplier_id = int(sup_input)
    else:
        match = re.search(r"\|\s*ID:\s*(\d+)\s*$", sup_input)
        if match: supplier_id = int(match.group(1))
    
    if not supplier_id or not session.get(Supplier, supplier_id):
        print("Invalid supplier.")
        return

    # 2. Header Information
    while True:
        po_number = safe_input("PO Number (e.g. PO-24-001): ")
        if not po_number:
            print("PO Number is required.")
            continue
            
        # Check uniqueness
        existing_po = session.query(PurchaseOrder).filter_by(po_number=po_number).first()
        if existing_po:
            print(f"Error: PO Number '{po_number}' already exists. Please choose another.")
        else:
            break
        
    date_str = safe_input("Date (YYYY-MM-DD) [Today]: ")
    po_date = datetime.utcnow()
    if date_str:
        try:
            po_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Using today.")

    expected_str = safe_input("Expected Date (YYYY-MM-DD): ")
    expected_date = None
    if expected_str:
         try:
            expected_date = datetime.strptime(expected_str, "%Y-%m-%d")
         except ValueError: pass

    payment_terms = safe_input("Payment Terms [Net 180]: ") or "Net 180"
    currency = safe_input("Currency [USD]: ") or "USD"
    
    # Defaults for Consignee/Notify
    our_company = session.query(OurCompany).first()
    default_consignee = our_company.company_name if our_company else "Our Company"
    
    # Shipping & Intl
    print("--- Shipping Details ---")
    
    # Ship To
    is_manual, val = select_address_source(session, "Ship To Address")
    if not is_manual and val is not None:
        ship_to = val
        print(f"Selected Ship To:\n{ship_to}")
    elif not is_manual and val is None:
         # User chose skip (which acts like empty/default here since it's new PO)
        ship_to = ""
    else:
        ship_to = safe_input("Ship To Address (Leave empty for default): ")

    method = safe_input("Shipping Method: ")
    incoterm = safe_input("Incoterm (e.g. CIF): ")
    port = safe_input("Port of Destination: ")
    
    # Consignee
    is_manual, val = select_address_source(session, "Consignee")
    if not is_manual and val is not None:
        consignee = val
        print(f"Selected Consignee:\n{consignee}")
    else:
        consignee = safe_input(f"Consignee [{default_consignee}]: ") or default_consignee

    # Notify
    is_manual, val = select_address_source(session, "Notify Party")
    if not is_manual and val is not None:
        notify = val
        print(f"Selected Notify Party:\n{notify}")
    else:
        notify = safe_input(f"Notify Party [{default_consignee}]: ") or default_consignee
        
    tc_party = safe_input("TC Party [Same as Consignee]: ") # Default to None/Blank implies logic elsewhere or explicit string
    if not tc_party: tc_party = "Same as Consignee"
    
    notes = safe_input("Notes: ")
    
    # 3. Line Items
    lines = []
    
    products = session.query(Product).all()
    prod_map = {f"{p.sku} - {p.name}": p for p in products}
    prod_completer = WordCompleter(list(prod_map.keys()), ignore_case=True, match_middle=True)
    
    while True:
        print(f"\n--- Add Line Item ({len(lines)} added) ---")
        try:
            p_input = prompt("Select Product (Empty to finish): ", completer=prod_completer)
        except KeyboardInterrupt: break
        
        if not p_input: break
        
        product = None
        if p_input in prod_map:
            product = prod_map[p_input]
        else:
             print("Please select a valid product.")
             continue
             
        qty_str = safe_input("Quantity: ")
        if not qty_str.isdigit():
             print("Invalid quantity.")
             continue
        qty = int(qty_str)
        
        unit = safe_input(f"Unit: ")
        
        default_cost = 0.0
        try:
             default_cost = float(product.cost_price)
        except (ValueError, TypeError):
             pass # Treat TBD as 0.0 for PO creation math
        
        cost_str = safe_input(f"Unit Cost [{default_cost}]: ")
        try:
            cost = float(cost_str) if cost_str else default_cost
        except ValueError:
            print("Invalid cost, defaulting to 0.0")
            cost = 0.0
        
        desc = safe_input(f"Description [{product.name}]: ") or product.name
        
        # Packing structure per line
        pack_line = safe_input("Packing Structure (e.g. 20kg Sacks): ")
        
        lines.append({
            "product_id": product.id,
            "qty": qty,
            "unit": unit,
            "cost": cost,
            "description": desc,
            "packing_structure": pack_line,
            "total": qty * cost
        })
        
    if not lines:
        print("No lines added. Aborting.")
        return

    # 4. Summary & Save
    total_goods = sum(l['total'] for l in lines)
    print(f"\nTotal Goods: ${total_goods:.2f}")
    
    try:
        ship_cost = float(safe_input("Shipping Cost [0.0]: ") or 0.0)
        discount = float(safe_input("Discount [0.0]: ") or 0.0)
        tax = float(safe_input("Tax [0.0]: ") or 0.0)
    except ValueError:
        ship_cost, discount, tax = 0.0, 0.0, 0.0
        
    grand_total = total_goods + ship_cost + tax - discount
    print(f"Grand Total: ${grand_total:.2f}")
    
    confirm = safe_input("Save Order? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
        
    # Create Objects
    po = PurchaseOrder(
        supplier_id=supplier_id,
        po_number=po_number,
        date=po_date,
        expected_date=expected_date,
        payment_terms=payment_terms,
        currency=currency,
        ship_to_address=ship_to,
        shipping_method=method,
        incoterm=incoterm,
        port_of_destination=port,
        # packing_structure=packing, # Removed
        consignee=consignee,
        notify_party=notify,
        tc_party=tc_party,
        notes=notes,
        shipping_cost=ship_cost,
        discount_amount=discount,
        tax_amount=tax,
        status='Draft'
    )
    
    for l in lines:
        po_line = PurchaseOrderLine(
            product_id=l['product_id'],
            qty=l['qty'],
            unit=l['unit'],
            cost=l['cost'],
            description=l['description'],
            packing_structure=l['packing_structure'] # Added
        )
        po.lines.append(po_line)
        
    session.add(po)
    session.commit()
    print(f"Purchase Order {po_number} created successfully (ID: {po.id}).")

def list_orders(session: Session):
    print("\n--- List Purchase Orders ---")
    pos = session.query(PurchaseOrder).all()
    if not pos:
        print("No purchase orders found.")
        return
        
    data = []
    for po in pos:
        total = sum(l.cost * l.qty for l in po.lines) + po.shipping_cost + po.tax_amount - po.discount_amount
        data.append([
            po.id, 
            po.po_number, 
            po.supplier.name, 
            po.date.strftime("%Y-%m-%d"), 
            po.status, 
            f"${total:.2f}"
        ])
    
    print_table(data, ["ID", "PO #", "Supplier", "Date", "Status", "Total"])

def view_order_details(session: Session):
    print("\n--- View Purchase Order ---")
    pos = session.query(PurchaseOrder).all()
    if not pos: return

    po_map = {f"{po.po_number} | {po.supplier.name}": po.id for po in pos}
    completer = WordCompleter(list(po_map.keys()), ignore_case=True, match_middle=True)
    
    try:
        user_input = prompt("Select PO: ", completer=completer)
    except KeyboardInterrupt: return
    
    if not user_input: return
    
    po_id = po_map.get(user_input)
    # Simple direct int fallback
    if not po_id and user_input.isdigit():
        po_id = int(user_input)
        
    po = session.get(PurchaseOrder, po_id)
    if not po: 
        print("PO not found.")
        return
        
    print(f"\nPO #:       {po.po_number} (ID: {po.id})")
    print(f"Supplier:   {po.supplier.name}")
    print(f"Date:       {po.date}")
    print(f"Status:     {po.status}")
    print(f"Terms:      {po.payment_terms}")
    print(f"Ship Via:   {po.shipping_method}")
    print(f"Incoterm:   {po.incoterm}")
    print(f"Port:       {po.port_of_destination}")
    print(f"Consignee:  {po.consignee}")
    print(f"Notify:     {po.notify_party}")
    print(f"TC Party:   {po.tc_party}")
    print(f"Ship To:    {po.ship_to_address or 'Default'}")
    print(f"Notes:      {po.notes}")
    
    print("\n--- Line Items ---")
    data = []
    for l in po.lines:
        data.append([
            l.product.sku,
            l.description,
            l.qty,
            l.unit,
            l.packing_structure, # Added to view
            f"${l.cost:.2f}",
            f"${(l.qty * l.cost):.2f}"
        ])
    print_table(data, ["SKU", "Description", "Qty", "Unit", "Packing", "Cost", "Total"])
    
    subtotal = sum(l.cost * l.qty for l in po.lines)
    print(f"\nSubtotal:   ${subtotal:.2f}")
    if po.discount_amount: print(f"Discount:  -${po.discount_amount:.2f}")
    if po.shipping_cost:   print(f"Shipping:  +${po.shipping_cost:.2f}")
    if po.tax_amount:      print(f"Tax:       +${po.tax_amount:.2f}")
    
    grand_total = subtotal + po.shipping_cost + po.tax_amount - po.discount_amount
    print(f"TOTAL:      ${grand_total:.2f}")
    
    print("\n")
    action = safe_input("Press [Enter] to go back, 'p' for PDF, 'e' to Edit: ")
    if action.lower() == 'p':
        # Need company info
        our_company = session.query(OurCompany).first()
        filepath = generate_po_pdf(po, our_company)
        print(f"PDF Generated: {filepath}")
        safe_input("Press Enter to continue...")
    elif action.lower() == 'e':
        edit_purchase_order(session, po)

def edit_purchase_order(session: Session, po: PurchaseOrder):
    print(f"\n--- Edit PO {po.po_number} ---")
    print("Press [Enter] to keep current value.")
    
    # 1. Status
    print(f"Current Status: {po.status}")
    new_status = safe_input("New Status (Draft/Sent/Accepted/Received/Cancelled/Closed): ")
    if new_status and new_status in ['Draft', 'Sent', 'Accepted', 'Received', 'Cancelled', 'Closed']:
        po.status = new_status
        
    # 2. Date
    d_str = safe_input(f"Date [{po.date.strftime('%Y-%m-%d')}]: ")
    if d_str:
        try:
             po.date = datetime.strptime(d_str, "%Y-%m-%d")
        except ValueError: print("Invalid date, keeping original.")
        
    # 3. Logistics
    po.payment_terms = safe_input(f"Terms [{po.payment_terms}]: ") or po.payment_terms
    po.shipping_method = safe_input(f"Ship Via [{po.shipping_method}]: ") or po.shipping_method
    
    # Ship To Edit
    print(f"Current Ship To: {po.ship_to_address or 'Default'}")
    is_manual, val = select_address_source(session, "Ship To")
    if not is_manual and val is not None:
        po.ship_to_address = val
    elif is_manual:
        new_val = safe_input("New Ship To (Enter to keep): ")
        if new_val: po.ship_to_address = new_val

    po.incoterm = safe_input(f"Incoterm [{po.incoterm}]: ") or po.incoterm
    po.port_of_destination = safe_input(f"Port [{po.port_of_destination}]: ") or po.port_of_destination
    
    # 4. Parties
    # Consignee
    print(f"Current Consignee: {po.consignee}")
    is_manual, val = select_address_source(session, "Consignee")
    if not is_manual and val is not None:
        po.consignee = val
    elif is_manual:
        new_val = safe_input("New Consignee (Enter to keep): ")
        if new_val: po.consignee = new_val

    # Notify
    print(f"Current Notify: {po.notify_party}")
    is_manual, val = select_address_source(session, "Notify Party")
    if not is_manual and val is not None:
        po.notify_party = val
    elif is_manual:
        new_val = safe_input("New Notify (Enter to keep): ")
        if new_val: po.notify_party = new_val
        
    po.tc_party = safe_input(f"TC Party [{po.tc_party}]: ") or po.tc_party
    
    # 5. Financials
    s_cost = safe_input(f"Shipping Cost [{po.shipping_cost}]: ")
    if s_cost: po.shipping_cost = float(s_cost)
    
    disc = safe_input(f"Discount [{po.discount_amount}]: ")
    if disc: po.discount_amount = float(disc)
    
    tax = safe_input(f"Tax [{po.tax_amount}]: ")
    if tax: po.tax_amount = float(tax)
    
    po.notes = safe_input(f"Notes [{po.notes}]: ") or po.notes
    
    try:
        session.commit()
        print("PO Updated Successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error updating PO: {e}")

def create_customer_order(session: Session):
     # Placeholder to match existing menu call not to break it? 
     # User asked for POs, but create_customer_order is called in menu. 
     # I should just implement create_purchase_order and ensure other undefined functions don't crash if they were missing.
     # Wait, existing code had create_customer_order commented or "..."? 
     # Line 348 was "# ... (Order functions unchanged)". Ah, I need to check if I am overwriting them.
     # The view_file 138 showed lines 347-348 were "# --- Order Management ---\n# ... (Order functions unchanged)".
     # That implies the view was truncated or I assumed they were there? 
     # Actually, in Step 138, lines 347-349 show "# --- Order Management ---\n# ... (Order functions unchanged)".
     # This means the previous `view_file` might have skipped the actual implementation or they were literally placeholders.
     # Let me check if create_customer_order exists.
     # Re-reading Step 138 content carefully...
     # Ah, line 439 calls `create_customer_order(session)`.
     # But line 348 says `(Order functions unchanged)`.
     # If the file content *actually* has them, I shouldn't overwrite them blindly.
     # The `view_file` tool *replaces* content in the thought block representation? No.
     # Step 138 output shows line 347-349.
     # If I overwrite 347-349, I might delete existing functions if they are there.
     # BUT, the view_file output in Step 138 literally shows `# ... (Order functions unchanged)`.
     # Wait, does that mean the file *contains* that comment, or the tool summarized it?
     # "The above content shows the entire, complete file contents" -> It seems the file *actually* has that comment if it was a copy-paste from a previous interaction?
     # OR, the `view_file` output in Step 138 lines 348 is suspicious.
     # Let me check the file content around line 348 again or assume I need to ADD these functions.
     # If `create_customer_order` is called in `order_menu` (line 439), it MUST be defined somewhere or the code crashes.
     # In line 439: `elif choice == '2': create_customer_order(session)`
     # If `create_customer_order` isn't defined, `main.py` is broken right now.
     # I see `models` imported in line 13.
     # Let's assume I need to PROVIDE these PO functions. 
     # I will define `create_customer_order` as a placeholder if it doesn't exist to prevent crash, OR
     # I will just add my PO functions and leave the rest.
     # Safest is to append my functions or replace the `# ...` placeholder.
     pass

def create_customer_order(session: Session):
    print("\n--- Create Customer Order ---")
    
    # 1. Select Customer
    customer = pick_customer(session)
    if not customer: return

    # 2. Header Information
    print(f"Customer: {customer.customer_name}")
    
    while True:
        inv_num = safe_input("Invoice Number (Optional, Unique): ")
        if inv_num:
            # Check uniqueness
            exists = session.query(CustomerOrder).filter_by(invoice_number=inv_num).first()
            if exists:
                print(f"Error: Invoice Number '{inv_num}' already exists.")
                continue
        break
        
    po_num = safe_input("PO Number (Customer's PO): ")
    
    date_str = safe_input("Date (YYYY-MM-DD) [Today]: ")
    co_date = datetime.utcnow()
    if date_str:
        try:
            co_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Using today.")

    tracking = safe_input("Tracking/Terms: ")
    notes = safe_input("Notes: ")
    
    # Addresses - Default to Customer's, allow override
    cust_bill = f"{customer.bill_to_addr1}\n{customer.bill_to_addr2 or ''}\n{customer.bill_to_city}, {customer.bill_to_state} {customer.bill_to_zip}\n{customer.bill_to_country}"
    cust_ship = f"{customer.ship_to_addr1}\n{customer.ship_to_addr2 or ''}\n{customer.ship_to_city}, {customer.ship_to_state} {customer.ship_to_zip}\n{customer.ship_to_country}"
    
    print("\n--- Bill To Address ---")
    print(f"Customer Default:\n{cust_bill}")
    use_def = safe_input("Use Default? (y/n) [y]: ").lower()
    if use_def == 'n':
        print("Enter Bill To Address (End with empty line):")
        lines = []
        while True:
            l = safe_input("")
            if not l: break
            lines.append(l)
        bill_to = "\n".join(lines)
    else:
        bill_to = cust_bill

    print("\n--- Ship To Address ---")
    print(f"Customer Default:\n{cust_ship}")
    use_def = safe_input("Use Default? (y/n) [y]: ").lower()
    if use_def == 'n':
        print("Enter Ship To Address (End with empty line):")
        lines = []
        while True:
            l = safe_input("")
            if not l: break
            lines.append(l)
        ship_to = "\n".join(lines)
    else:
        ship_to = cust_ship
        
    # 3. Line Items
    co_lines = []
    products = session.query(Product).all()
    prod_map = {f"{p.sku} - {p.name}": p for p in products}
    prod_completer = WordCompleter(list(prod_map.keys()), ignore_case=True, match_middle=True)
    
    while True:
        print(f"\n--- Add Line Item ({len(co_lines)} added) ---")
        try:
            p_input = prompt("Select Product (Empty to finish): ", completer=prod_completer)
        except KeyboardInterrupt: break
        
        if not p_input: break
        
        product = None
        if p_input in prod_map:
            product = prod_map[p_input]
        else:
            print("Please select a valid product.")
            continue
            
        qty_str = safe_input("Quantity: ")
        if not qty_str.isdigit():
             print("Invalid quantity.")
             continue
        qty = int(qty_str)
        
        unit = safe_input(f"Unit: ")
        
        default_price = 0.0
        try:
             default_price = float(product.unit_price)
        except (ValueError, TypeError):
             pass
        
        price_str = safe_input(f"Unit Price [{default_price}]: ")
        try:
            price = float(price_str) if price_str else default_price
        except ValueError:
            price = 0.0
            
        desc = safe_input(f"Description [{product.name}]: ") or product.name
        
        amount = qty * price
        
        co_lines.append({
            "product_id": product.id,
            "qty": qty,
            "unit": unit,
            "selling_price": price,
            "description": desc,
            "amount": amount
        })
        
    if not co_lines:
        print("No lines added. Aborting.")
        return

    # 4. Financials
    subtotal = sum(l['amount'] for l in co_lines)
    print(f"\nSubtotal: ${subtotal:.2f}")
    
    try:
        shipping = float(safe_input("Shipping Cost [0.0]: ") or 0.0)
        discount = float(safe_input("Discount [0.0]: ") or 0.0)
        paid = float(safe_input("Amount Paid [0.0]: ") or 0.0)
        credit = float(safe_input("Credit Applied [0.0]: ") or 0.0)
    except ValueError:
        print("Invalid number.")
        return

    # Create Object
    co = CustomerOrder(
        customer_id=customer.id,
        invoice_number=inv_num,
        po_number=po_num,
        date=co_date,
        tracking_terms=tracking,
        notes=notes,
        bill_to_address=bill_to,
        ship_to_address=ship_to,
        shipping=shipping,
        discount=discount,
        amount_paid=paid,
        credit=credit,
        status='Pending'
    )
    
    for l in co_lines:
        line = CustomerOrderLine(
            product_id=l['product_id'],
            qty=l['qty'],
            unit=l['unit'],
            selling_price=l['selling_price'],
            description=l['description'],
            amount=l['amount']
        )
        co.lines.append(line)
        
    try:
        session.add(co)
        session.commit()
        print(f"Customer Order created successfully (ID: {co.id}).")
    except Exception as e:
        session.rollback()
        print(f"Error saving order: {e}")

def list_customer_orders(session: Session):
    print("\n--- List Customer Orders ---")
    orders = session.query(CustomerOrder).all()
    if not orders:
        print("No orders found.")
        return
        
    data = []
    for co in orders:
        subtotal = sum(l.amount for l in co.lines)
        total = subtotal + co.shipping - co.discount - co.credit
        data.append([
            co.id,
            co.date.strftime("%Y-%m-%d"),
            co.customer.customer_name,
            co.invoice_number or "N/A",
            co.status,
            f"${total:.2f}"
        ])
    print_table(data, ["ID", "Date", "Customer", "Inv #", "Status", "Total"])

def view_customer_order(session: Session):
    print("\n--- View Customer Order ---")
    orders = session.query(CustomerOrder).all()
    if not orders: return
    
    # Map by Invoice # if exists, or ID/Customer
    order_map = {}
    for o in orders:
        label = f"ID:{o.id} | {o.customer.customer_name}"
        if o.invoice_number:
            label += f" | Inv: {o.invoice_number}"
        order_map[label] = o.id
        
    completer = WordCompleter(list(order_map.keys()), ignore_case=True, match_middle=True)
    
    try:
        user_input = prompt("Select Order: ", completer=completer)
    except KeyboardInterrupt: return
    if not user_input: return
    
    co_id = None
    if user_input in order_map:
        co_id = order_map[user_input]
    elif user_input.isdigit():
        co_id = int(user_input)
    else:
         match = re.search(r"ID:(\d+)", user_input)
         if match: co_id = int(match.group(1))
         
    co = session.get(CustomerOrder, co_id)
    if not co: return
    
    print(f"\nOrder ID:    {co.id}")
    print(f"Customer:    {co.customer.customer_name}")
    print(f"Date:        {co.date}")
    print(f"Status:      {co.status}")
    print(f"Invoice #:   {co.invoice_number}")
    print(f"PO Number:   {co.po_number}")
    print(f"Tracking:    {co.tracking_terms}")
    print(f"Bill To:\n{co.bill_to_address}")
    print(f"Ship To:\n{co.ship_to_address}")
    print(f"Notes:       {co.notes}")
    
    print("\n--- Line Items ---")
    data = []
    for i, l in enumerate(co.lines, 1):
        data.append([
            i,
            l.product.sku,
            l.description,
            l.qty,
            l.unit,
            f"${l.selling_price:.2f}",
            f"${l.amount:.2f}"
        ])
    print_table(data, ["#", "SKU", "Desc", "Qty", "Unit", "Price", "Amount"])
    
    # Totals
    subtotal = sum(l.amount for l in co.lines)
    total = subtotal + co.shipping - co.discount - co.credit
    
    print(f"\nSubtotal:    ${subtotal:.2f}")
    if co.shipping: print(f"Shipping:   +${co.shipping:.2f}")
    if co.discount: print(f"Discount:   -${co.discount:.2f}")
    if co.credit:   print(f"Credit:     -${co.credit:.2f}")
    print(f"TOTAL:       ${total:.2f}")
    if co.amount_paid: print(f"Paid:       -${co.amount_paid:.2f}")
    print(f"Balance Due: ${(total - co.amount_paid):.2f}")
    
    print("\n")
    action = safe_input("Press [Enter] to go back, 'e' to Edit: ")
    if action.lower() == 'e':
        edit_customer_order(session, co)

def edit_customer_order(session: Session, co: CustomerOrder):
    print(f"\n--- Edit Customer Order {co.id} ---")
    print("Press [Enter] to keep current value.")
    
    inv_num = safe_input(f"Invoice Number [{co.invoice_number}]: ")
    if inv_num: co.invoice_number = inv_num
    
    po_num = safe_input(f"PO Number [{co.po_number}]: ")
    if po_num: co.po_number = po_num
    
    d_str = safe_input(f"Date [{co.date.strftime('%Y-%m-%d')}]: ")
    if d_str:
        try:
            co.date = datetime.strptime(d_str, "%Y-%m-%d")
        except: pass
        
    co.tracking_terms = safe_input(f"Tracking [{co.tracking_terms}]: ") or co.tracking_terms
    
    # Financials
    ship = safe_input(f"Shipping [{co.shipping}]: ")
    if ship: co.shipping = float(ship)
    
    disc = safe_input(f"Discount [{co.discount}]: ")
    if disc: co.discount = float(disc)
    
    paid = safe_input(f"Paid [{co.amount_paid}]: ")
    if paid: co.amount_paid = float(paid)
    
    cred = safe_input(f"Credit [{co.credit}]: ")
    if cred: co.credit = float(cred)
    
    co.notes = safe_input(f"Notes [{co.notes}]: ") or co.notes
    
    # Address Editing? Maybe too complex for single field.
    change_addr = safe_input("Edit Addresses? (y/n) [n]: ")
    if change_addr.lower() == 'y':
        print("--- Bill To ---")
        print(f"Current:\n{co.bill_to_address}\n")
        print("Enter New Bill To (Empty line to finish):")
        lines = []
        while True:
            l = safe_input("")
            if not l: break
            lines.append(l)
        if lines: co.bill_to_address = "\n".join(lines)
        
        print("--- Ship To ---")
        print(f"Current:\n{co.ship_to_address}\n")
        print("Enter New Ship To (Empty line to finish):")
        lines = []
        while True:
             l = safe_input("")
             if not l: break
             lines.append(l)
        if lines: co.ship_to_address = "\n".join(lines)

    try:
        session.commit()
        print("Order Updated.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")


# --- Menus ---

def main_menu():
    print("\n=== PYTHON ERP SYSTEM ===")
    print("1. Manage Data (Products, Customers, Suppliers)")
    print("2. Order Management (PO, CO)")
    print("3. Invoicing (Convert, Print PDF)")
    print("4. Documents (Upload)")
    print("5. Exit")
    return safe_input("Select Option: ")

def data_menu(session: Session):
    while True:
        print("\n--- Manage Data ---")
        print("1. Manage Product Data")
        print("2. Manage Customer Data")
        print("3. Manage Supplier Data")
        print("9. Main Menu")
        print("0. Back")
        
        choice = safe_input("Select: ")
        if choice == '1':
            if product_menu(session) == "main": return "main"
        elif choice == '2':
            if customer_menu(session) == "main": return "main"
        elif choice == '3':
            if supplier_menu(session) == "main": return "main"
        elif choice == '9': return "main"
        elif choice == '0': break

def product_menu(session: Session):
    while True:
        print("\n--- Manage Product Data ---")
        print("1. Add Product")
        print("2. List Products")
        print("3. View Product Details")
        print("9. Main Menu")
        print("0. Back")
        
        choice = safe_input("Select: ")
        if choice == '1': add_product(session)
        elif choice == '2': list_products(session)
        elif choice == '3': view_product_details(session)
        elif choice == '9': return "main"
        elif choice == '0': break

def customer_menu(session: Session):
    while True:
        print("\n--- Manage Customer Data ---")
        print("1. Add Customer")
        print("2. List Customers")
        print("3. View Customer Details")
        print("9. Main Menu")
        print("0. Back")
        
        choice = safe_input("Select: ")
        if choice == '1': add_customer(session)
        elif choice == '2': list_customers(session)
        elif choice == '3': view_customer_details(session)
        elif choice == '9': return "main"
        elif choice == '0': break

def supplier_menu(session: Session):
    while True:
        print("\n--- Manage Supplier Data ---")
        print("1. Add Supplier")
        print("2. List Suppliers")
        print("3. View Supplier Details")
        print("9. Main Menu")
        print("0. Back")
        
        choice = safe_input("Select: ")
        if choice == '1': add_supplier(session)
        elif choice == '2': list_suppliers(session)
        elif choice == '3': view_supplier_details(session)
        elif choice == '9': return "main"
        elif choice == '0': break

def order_menu(session: Session):
    while True:
        print("\n--- Order Management ---")
        print("1. Create Purchase Order")
        print("2. Create Customer Order")
        print("3. List Purchase Orders")
        print("4. List Customer Orders")
        print("5. View Purchase Order Details")
        print("6. View Customer Order Details")
        print("9. Main Menu")
        print("0. Back")
        
        choice = safe_input("Select: ")
        if choice == '1': create_purchase_order(session)
        elif choice == '2': create_customer_order(session)
        elif choice == '3': list_orders(session)
        elif choice == '4': list_customer_orders(session)
        elif choice == '5': view_order_details(session)
        elif choice == '6': view_customer_order(session)
        elif choice == '9': return "main"
        elif choice == '0': break

def invoice_menu(session: Session):
    while True:
        print("\n--- Invoicing ---")
        print("1. Convert CO to Invoice")
        print("2. Generate PDF for Invoice")
        print("9. Main Menu")
        print("0. Back")
        
        choice = safe_input("Select: ")
        if choice == '1': convert_co_to_invoice(session)
        elif choice == '2': generate_pdf_wrapper(session)
        elif choice == '9': return "main"
        elif choice == '0': break

def run():
    ensure_directories()
    
    # DB Setup
    try:
        engine = get_engine()
        init_db(engine)
        session = get_session(engine)
    except Exception as e:
        print(f"Database Error: {e}")
        print("Please check your database configuration in models.py")
        return

    while True:
        choice = main_menu()
        if choice == '1':
            data_menu(session)
        elif choice == '2':
            order_menu(session)
        elif choice == '3':
            invoice_menu(session)
        elif choice == '4':
            upload_document(session)
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    run()
