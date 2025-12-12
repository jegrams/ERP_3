from fpdf import FPDF
import os
from datetime import datetime

class PurchaseOrderPDF(FPDF):
    def __init__(self, po, our_company):
        super().__init__()
        self.po = po
        self.our_company = our_company
        self.logo_path = os.path.join("assets", "media", "mana-organics-IVTF Ver 3.png")

    def header(self):
        # Logo (Top Left)
        if os.path.exists(self.logo_path):
            self.image(self.logo_path, 10, 8, 40) # Smaller, Left
        
        # Company Info (Below Logo)
        # Assuming logo height ~15-20, start info at y=30
        self.set_xy(10, 30)
        
        self.set_font('Arial', 'B', 12)
        company_name = self.our_company.company_name if self.our_company else "My Company"
        self.cell(100, 5, company_name, ln=True)
        
        self.set_font('Arial', '', 9)
        if self.our_company:
            addr = f"{self.our_company.address1 or ''} {self.our_company.address2 or ''}"
            csz = f"{self.our_company.city or ''}, {self.our_company.state or ''} {self.our_company.zip_code or ''}"
            country = self.our_company.country or ""
            phone = f"Phone: {self.our_company.phone}" if self.our_company.phone else ""
            email = f"Email: {self.our_company.email}" if self.our_company.email else ""
            
            self.cell(100, 4, addr.strip(), ln=True)
            self.cell(100, 4, csz.strip(), ln=True)
            if country: self.cell(100, 4, country, ln=True)
            if phone: self.cell(100, 4, phone, ln=True)
            if email: self.cell(100, 4, email, ln=True)
        else:
            self.cell(100, 4, "Address Line 1", ln=True)
        
        # Title (Top Right)
        self.set_xy(120, 10)
        self.set_font('Arial', 'B', 24)
        self.cell(80, 10, 'PURCHASE ORDER', align='R', ln=True)
        
        self.line(10, 60, 200, 60) # Divider line lower down
        self.set_y(65)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    def chapter_body(self):
        po = self.po
        
        # --- 1. Order Details Grid ---
        self.set_font('Arial', '', 10)
        
        # Helper to print a label-value pair
        def print_field(label, value, x_offset=0, y_offset=0):
            self.set_xy(x_offset, y_offset)
            self.set_font('Arial', 'B', 10)
            self.cell(35, 5, label, 0)
            self.set_font('Arial', '', 10)
            self.cell(50, 5, str(value or ""), 0)

        start_y = self.get_y()
        # Row 1
        print_field("PO Number:", po.po_number, 10, start_y)
        print_field("Date:", po.date.strftime('%Y-%m-%d'), 110, start_y)
        
        # Row 2
        print_field("Vendor Ref:", po.vendor_reference, 10, start_y + 6)
        print_field("Terms:", po.payment_terms, 110, start_y + 6)
        
        # Row 3
        print_field("Shipping Method:", po.shipping_method, 10, start_y + 12)
        print_field("Exp. Date:", po.expected_date.strftime('%Y-%m-%d') if po.expected_date else "", 110, start_y + 12)

        self.ln(10) # Reduced from 20 to 10

        # --- 2. Addresses ---
        y_addr = self.get_y()
        self.set_font('Arial', 'B', 11)
        self.cell(95, 6, "VENDOR", 0, 0)
        self.cell(95, 6, "SHIP TO", 0, 1)
        
        self.set_font('Arial', '', 10)
        # Vendor Block
        v_y = self.get_y()
        self.set_xy(10, v_y)
        supplier = po.supplier
        self.multi_cell(90, 5, f"{supplier.name}\n{supplier.contact_name or ''}\n{supplier.address1 or ''}\n{supplier.city or ''} {supplier.state or ''}\n{supplier.country or ''}\n{supplier.phone or ''}")
        v_end_y = self.get_y()
        
        # Ship To Block
        self.set_xy(105, v_y)
        if po.ship_to_address:
            self.multi_cell(90, 5, po.ship_to_address)
        else:
            # Default to Our Company
             if self.our_company:
                 self.multi_cell(90, 5, f"{self.our_company.company_name}\n{self.our_company.address1 or ''}\n{self.our_company.city or ''} {self.our_company.state or ''}\n{self.our_company.country or ''}")
             else:
                 self.multi_cell(90, 5, "Same as User Company")
        s_end_y = self.get_y()

        self.set_y(ma(v_end_y, s_end_y) + 5) # Ensure enough space
        self.ln(5)

        # --- 3. Logistics & Intl ---
        self.set_font('Arial', 'B', 10)
        self.cell(0, 6, "LOGISTICS & SHIPPING DETAILS", 'B', 1)
        self.ln(2)
        
        l_y = self.get_y()
        print_field("Incoterm:", po.incoterm, 10, l_y)
        print_field("Port of Dest:", po.port_of_destination, 110, l_y)
        
        # Dynamic Spacing for Consignee / Notify
        c_n_y = l_y + 8 # Start slightly lower
        
        # Consignee
        print_field("Consignee:", "", 10, c_n_y)
        self.set_xy(35, c_n_y)
        self.set_font('Arial', '', 9)
        self.multi_cell(65, 4, str(po.consignee or ""))
        c_end = self.get_y()
        
        # Notify
        print_field("Notify Party:", "", 110, c_n_y)
        self.set_xy(135, c_n_y)
        self.set_font('Arial', '', 9)
        self.multi_cell(65, 4, str(po.notify_party or ""))
        n_end = self.get_y()
        
        # TC Party starts after the tallest of the previous blocks
        tc_start_y = ma(c_end, n_end) + 6
        
        print_field("TC Party:", "", 10, tc_start_y)
        self.set_xy(35, tc_start_y)
        self.set_font('Arial', '', 9)
        self.multi_cell(65, 4, str(po.tc_party or ""))
        tc_end = self.get_y()
        
        self.set_y(tc_end + 8)


        # --- 4. Line Items Table ---
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(220, 220, 220)
        
        # Headers: SKU (20), Description (72), Packing (32), Qty (12), Unit (12), Price (21), Total (21)
        self.cell(20, 6, "SKU", 1, 0, 'C', True)
        self.cell(72, 6, "Description", 1, 0, 'C', True)
        self.cell(32, 6, "Packing", 1, 0, 'C', True)
        self.cell(12, 6, "Qty", 1, 0, 'C', True)
        self.cell(12, 6, "Unit", 1, 0, 'C', True)
        self.cell(21, 6, "Unit Price", 1, 0, 'C', True)
        self.cell(21, 6, "Total", 1, 1, 'C', True)
        
        self.set_font('Arial', '', 9)
        subtotal = 0.0
        
        for line in po.lines:
            line_total = line.cost * line.qty
            subtotal += line_total
            
            # Description Priority: Product.description > Line.description > Product.name
            desc_text = line.product.description or line.description or line.product.name or ""
            
            self.cell(20, 6, str(line.product.sku), 1)
            self.cell(72, 6, str(desc_text)[:50], 1) # Increased truncate limit
            self.cell(32, 6, str(line.packing_structure or "")[:20], 1)
            self.cell(12, 6, str(line.qty), 1, 0, 'C')
            self.cell(12, 6, str(line.unit or ""), 1, 0, 'C')
            self.cell(21, 6, f"{po.currency} {line.cost:.2f}", 1, 0, 'R')
            self.cell(21, 6, f"{line_total:.2f}", 1, 1, 'R')
            
        self.ln(5)

        # --- 5. Totals ---
        self.set_x(130)
        self.set_font('Arial', 'B', 10)
        self.cell(35, 6, "Subtotal:", 0, 0, 'R')
        self.set_font('Arial', '', 10)
        self.cell(25, 6, f"{po.currency} {subtotal:.2f}", 0, 1, 'R')
        
        if po.discount_amount:
            self.set_x(130)
            self.set_font('Arial', 'B', 10)
            self.cell(35, 6, "Discount:", 0, 0, 'R')
            self.set_font('Arial', '', 10)
            self.cell(25, 6, f"- {po.discount_amount:.2f}", 0, 1, 'R')

        if po.shipping_cost:
            self.set_x(130)
            self.set_font('Arial', 'B', 10)
            self.cell(35, 6, "Shipping:", 0, 0, 'R')
            self.set_font('Arial', '', 10)
            self.cell(25, 6, f"+ {po.shipping_cost:.2f}", 0, 1, 'R')
            
        if po.tax_amount:
            self.set_x(130)
            self.set_font('Arial', 'B', 10)
            self.cell(35, 6, "Tax:", 0, 0, 'R')
            self.set_font('Arial', '', 10)
            self.cell(25, 6, f"+ {po.tax_amount:.2f}", 0, 1, 'R')
            
        self.ln(2)
        grand_total = subtotal + po.shipping_cost + po.tax_amount - po.discount_amount
        
        self.set_x(130)
        self.set_font('Arial', 'B', 12)
        self.cell(35, 8, "TOTAL:", 'T', 0, 'R')
        self.cell(25, 8, f"{po.currency} {grand_total:.2f}", 'T', 1, 'R')
        
        # --- 6. Notes & Footer ---
        self.ln(10)
        if po.notes:
            self.set_font('Arial', 'B', 10)
            self.cell(0, 5, "Notes:", 0, 1)
            self.set_font('Arial', '', 10)
            self.multi_cell(0, 5, po.notes)
            self.ln(10)
            
        # Signature
        self.ln(10)
        self.cell(100, 5, "_"*40, 0, 1)
        self.cell(100, 5, f"Authorized Signature ({po.created_by or 'Manager'})", 0, 1)

def ma(a, b):
    return a if a > b else b

def generate_po_pdf(po, our_company, output_folder='./erp_pdfs/'):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    pdf = PurchaseOrderPDF(po, our_company)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.chapter_body()
    
    import time
    timestamp = int(time.time())
    filename = f"PO_{po.po_number}_{po.supplier.name.replace(' ', '_')}_{timestamp}.pdf"
    # cleanup filename
    filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '.', '_')]).strip()
    filepath = os.path.join(output_folder, filename)
    
    pdf.output(filepath)
    return filepath
