from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 20)
        self.cell(0, 10, 'INVOICE', align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

def generate_invoice_pdf(invoice_data, output_folder='./erp_pdfs/'):
    """
    Generates a PDF for an invoice.
    
    invoice_data should be a dict with:
        - id: int
        - type: str
        - date: datetime
        - customer_name: str
        - lines: list of dicts {'description', 'qty', 'unit_price', 'total'}
        - total_amount: float
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)

    # Invoice Details
    pdf.cell(0, 10, f"Invoice #: {invoice_data['id']}", ln=True)
    pdf.cell(0, 10, f"Type: {invoice_data['type']}", ln=True)
    pdf.cell(0, 10, f"Date: {invoice_data['date'].strftime('%Y-%m-%d')}", ln=True)
    pdf.cell(0, 10, f"Customer: {invoice_data['customer_name']}", ln=True)
    pdf.ln(10)

    # Table Header
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(80, 10, "Description", border=1)
    pdf.cell(30, 10, "Qty", border=1, align='C')
    pdf.cell(40, 10, "Unit Price", border=1, align='R')
    pdf.cell(40, 10, "Total", border=1, align='R')
    pdf.ln()

    # Table Rows
    pdf.set_font("helvetica", size=12)
    for line in invoice_data['lines']:
        pdf.cell(80, 10, str(line['description']), border=1)
        pdf.cell(30, 10, str(line['qty']), border=1, align='C')
        pdf.cell(40, 10, f"{line['unit_price']:.2f}", border=1, align='R')
        pdf.cell(40, 10, f"{line['total']:.2f}", border=1, align='R')
        pdf.ln()

    # Total
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(150, 10, "Total Amount:", border=1, align='R')
    pdf.cell(40, 10, f"{invoice_data['total_amount']:.2f}", border=1, align='R')
    
    filename = f"Invoice_{invoice_data['id']}_{invoice_data['customer_name'].replace(' ', '_')}.pdf"
    filepath = os.path.join(output_folder, filename)
    pdf.output(filepath)
    return filepath
