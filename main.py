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
    Invoice, InvoiceLine, Document
)
from pdf_generator import generate_invoice_pdf

# --- Setup & Helpers ---

DOCS_DIR = "./erp_documents/"
PDFS_DIR = "./erp_pdfs/"

def ensure_directories():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(PDFS_DIR, exist_ok=True)

def print_table(data, headers):
    print(tabulate(data, headers=headers, tablefmt="grid"))

# --- Core CRUD ---

def add_supplier(session: Session):
    print("\n--- Add Supplier ---")
    name = input("Name: ")
    contact_name = input("Contact Name: ")
    email = input("Email: ")
    phone = input("Phone: ")
    tax_id = input("Tax ID: ")
    
    print("--- Shipping/Physical Address ---")
    address1 = input("Address Line 1: ")
    address2 = input("Address Line 2: ")
    city = input("City: ")
    state = input("State: ")
    zip_code = input("Zip: ")
    country = input("Country: ")
    
    print("--- Billing Address ---")
    bill_to_addr1 = input("Address Line 1: ")
    bill_to_addr2 = input("Address Line 2: ")
    bill_to_city = input("City: ")
    bill_to_state = input("State: ")
    bill_to_zip = input("Zip: ")
    bill_to_country = input("Country: ")
    
    print("--- Notes ---")
    print("Enter notes (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
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
    customer_name = input("Customer Name: ")
    contact_name = input("Contact Name: ")
    email_address = input("Email Address: ")
    ship_to_phone = input("Ship To Phone: ")
    
    print("--- Shipping Address ---")
    ship_to_addr1 = input("Address Line 1: ")
    ship_to_addr2 = input("Address Line 2: ")
    ship_to_city = input("City: ")
    ship_to_state = input("State: ")
    ship_to_zip = input("Zip: ")
    ship_to_country = input("Country: ")
    
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

def view_customer_details(session: Session):
    print("\n--- View Customer Details (Active Search) ---")
    
    # 1. Load all customers for the completer
    customers = session.query(Customer).all()
    if not customers:
        print("No customers found in database.")
        return

    # 2. Prepare the list of choices: "Name | ID: <id>"
    #    We use a format easy to parse back.
    #    Using a dictionary map might be safer effectively, but completer needs strings.
    customer_map = {f"{c.customer_name} | ID: {c.id}": c.id for c in customers}
    choices = list(customer_map.keys())

    completer = WordCompleter(choices, ignore_case=True, match_middle=True)

    print("Start typing to search... (Press Tab/Arrows to select, Enter to confirm)")
    try:
        user_input = prompt("Customer: ", completer=completer)
    except KeyboardInterrupt:
        print("Cancelled.")
        return

    if not user_input:
        return

    # 3. Resolve the selection
    cust_id = None
    
    # Case A: User selected a valid option from the list (exact match)
    if user_input in customer_map:
        cust_id = customer_map[user_input]
    
    # Case B: User typed an ID directly (fallback)
    elif user_input.isdigit():
        cust_id = int(user_input)
    
    # Case C: User typed something else. We try to extract ID from string if format matches key 
    #         "Name | ID: 123" -> regex
    else:
        # Try to parse " | ID: 123" at end
        match = re.search(r"\|\s*ID:\s*(\d+)\s*$", user_input)
        if match:
            cust_id = int(match.group(1))
        else:
            print("Invalid selection. Please select a customer from the list.")
            return

    # 4. Fetch and Display
    c = session.get(Customer, cust_id)
    if not c:
        print(f"Customer with ID {cust_id} not found.")
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

def add_product(session: Session):
    print("\n--- Add Product ---")
    sku = input("SKU: ")
    name = input("Name: ")
    desc = input("Description: ")
    try:
        price = float(input("Unit Price: "))
    except ValueError:
        print("Invalid price.")
        return
    
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
# ... (Order functions unchanged)

# --- Menus ---

def main_menu():
    print("\n=== PYTHON ERP SYSTEM ===")
    print("1. Manage Data (Products, Customers, Suppliers)")
    print("2. Order Management (PO, CO)")
    print("3. Invoicing (Convert, Print PDF)")
    print("4. Documents (Upload)")
    print("5. Exit")
    return input("Select Option: ")

def data_menu(session: Session):
    while True:
        print("\n--- Manage Data ---")
        print("1. Manage Product Data")
        print("2. Manage Customer Data")
        print("3. Manage Supplier Data")
        print("9. Main Menu")
        print("0. Back")
        
        choice = input("Select: ")
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
        
        choice = input("Select: ")
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
        
        choice = input("Select: ")
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
        
        choice = input("Select: ")
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
        print("3. List All Orders")
        print("9. Main Menu")
        print("0. Back")
        
        choice = input("Select: ")
        if choice == '1': create_purchase_order(session)
        elif choice == '2': create_customer_order(session)
        elif choice == '3': list_orders(session)
        elif choice == '9': return "main"
        elif choice == '0': break

def invoice_menu(session: Session):
    while True:
        print("\n--- Invoicing ---")
        print("1. Convert CO to Invoice")
        print("2. Generate PDF for Invoice")
        print("9. Main Menu")
        print("0. Back")
        
        choice = input("Select: ")
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
