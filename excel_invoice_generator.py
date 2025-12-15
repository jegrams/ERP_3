
import os
import openpyxl
from openpyxl.utils import cell as cell_utils
from models import CustomerOrder

try:
    import win32com.client
    import pythoncom
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: 'pywin32' not installed. PDF export will be skipped.")

TEMPLATE_PATH = r'c:\Users\jegra\MyPython\ERP_3\assets\other\invoice_template.xlsx'
DOCS_DIR = r'c:\Users\jegra\MyPython\ERP_3\erp_documents'
PDFS_DIR = r'c:\Users\jegra\MyPython\ERP_3\erp_pdfs'

def set_named_range_value(wb, sheet, name, value):
    """
    Sets the value of a named range.
    Assumes the name refers to a single cell or we write to the top-left.
    """
    if name in wb.defined_names:
        d = wb.defined_names[name]
        # DefinedName.attr_text usually looks like 'Sheet1!$A$1' or just '$A$1' if local
        # We need to parse it. 
        # However, openpyxl handling of defined names can be tricky if they are scoped.
        
        dest = None
        # d.destinations returns generator of (worksheet_title, cell_range_string)
        # Verify if it works for global names
        try:
            dests = list(d.destinations)
            if dests:
                sheet_result, cell_range = dests[0]
                # If sheet_title is in destination, use it, else use active or passed sheet
                target_sheet = wb[sheet_result] if sheet_result in wb else sheet
                
                # cell_range could be "$A$1" or "$A$1:$B$2"
                # We interpret it as top-left cell
                if ':' in cell_range:
                    cell_ref = cell_range.split(':')[0]
                else:
                    cell_ref = cell_range
                
                # Strip $
                cell_ref = cell_ref.replace('$', '')
                target_sheet[cell_ref].value = value
                return True
        except Exception as e:
            print(f"Error setting {name}: {e}")
            return False
    else:
        print(f"Warning: Named range '{name}' not found.")
        return False

def generate_invoice(session, customer_order_id):
    co = session.get(CustomerOrder, customer_order_id)
    if not co:
        print("Order not found.")
        return

    print(f"Generating invoice for Order {co.id}...")
    
    try:
        wb = openpyxl.load_workbook(TEMPLATE_PATH)
        sheet = wb.active # Default to active sheet
        
        # 1. Header Fields
        # Maps {NamedRange: Value}
        data_map = {
            "Invoice_num": co.invoice_number or "",
            "PO_num": co.po_number or "",
            "Date": co.date.strftime("%Y-%m-%d") if co.date else "",
            "tracking_terms": co.tracking_terms or "",
            "Bill_To_address": co.bill_to_address or "",
            "Ship_To__If_different_than_billing": co.ship_to_address or "",
            "Shipping": co.shipping,
            "Discount": co.discount,
            "Credit": co.credit,
            "Paid": co.amount_paid,
            # "notes": co.notes # User list in prompt didn't strictly include 'notes', but common. I'll check user list again.
            # Step 110 list: ... tracking_terms, Unit_1...9, Unit_price...
            # The list in Step 32 DID verify naming. 
            # Wait, "Desc_1...9" is in list. "notes" is NOT in the list in Step 32.
            # But "tracking_terms" IS. 
            # I will skip notes if not requested by name, or check if it exists in template? 
            # User said "Please also add any additional fields you believe are necessary."
        }
        
        for k, v in data_map.items():
            set_named_range_value(wb, sheet, k, v)
            
        # 2. Line Items
        # Loop 1 to 9
        lines = co.lines
        for i in range(1, 10):
            if i <= len(lines):
                line = lines[i-1]
                qty = line.qty
                unit = line.unit or ""
                desc = line.description or line.product.name
                price = line.selling_price
                amount = line.amount
            else:
                # Clear empty lines
                qty = ""
                unit = ""
                desc = ""
                price = ""
                amount = ""
            
            set_named_range_value(wb, sheet, f"Quantity_{i}", qty)
            set_named_range_value(wb, sheet, f"Unit_{i}", unit)
            set_named_range_value(wb, sheet, f"Desc_{i}", desc)
            set_named_range_value(wb, sheet, f"Unit_price_{i}", price)
            set_named_range_value(wb, sheet, f"Amount_{i}", amount)
            
        # 3. Totals
        # Subtotal
        subtotal = sum(l.amount for l in lines)
        set_named_range_value(wb, sheet, "subtotal", subtotal)
        
        # Current Amount Due
        # Logic: Subtotal + Shipping + Tax (if any? User didn't request) - Discount - Credit - Paid
        # User requested "Current_Amount_Due".
        # Note: Tax was not in the named range list provided in Step 32. So I ignore it?
        # But 'shipping' and 'Discount' are.
        total_due = subtotal + co.shipping - co.discount - co.credit - co.amount_paid
        set_named_range_value(wb, sheet, "Current_Amount_Due", total_due)

        # 4. Save Excel
        # Filename: "Invoice {Invoice Number} - {Customer Name}.xlsx"
        inv_str = co.invoice_number or f"Order_{co.id}"
        # Sanitize
        safe_inv = "".join(c for c in inv_str if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_cust = "".join(c for c in co.customer.customer_name if c.isalnum() or c in (' ', '-', '_')).strip()
        
        filename = f"Invoice {safe_inv} - {safe_cust}"
        xlsx_path = os.path.join(DOCS_DIR, f"{filename}.xlsx")
        
        wb.save(xlsx_path)
        print(f"Excel Invoice saved to: {xlsx_path}")
        
        # 5. PDF Export
        if PDF_SUPPORT:
            pdf_path = os.path.join(PDFS_DIR, f"{filename}.pdf")
            export_to_pdf(xlsx_path, pdf_path)
        else:
            print("PDF export skipped (Missing pywin32 library).")
        
    except Exception as e:
        print(f"Error generating invoice: {e}")

def export_to_pdf(xlsx_path, pdf_path):
    print("Exporting to PDF...")
    try:
        # Need absolute paths for COM
        abs_xlsx = os.path.abspath(xlsx_path)
        abs_pdf = os.path.abspath(pdf_path)
        
        pythoncom.CoInitialize()
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        try:
            wb_com = excel.Workbooks.Open(abs_xlsx)
            # xlTypePDF = 0
            wb_com.ExportAsFixedFormat(0, abs_pdf)
            wb_com.Close(False)
            print(f"PDF saved to: {pdf_path}")
        except Exception as e:
            print(f"Excel COM Error: {e}")
        finally:
            excel.Quit()
            
    except Exception as e:
        print(f"PDF Export failed (requires Excel installed): {e}")
