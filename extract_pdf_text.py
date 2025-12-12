from pypdf import PdfReader

pdf_path = r"c:\Users\jegra\MyPython\ERP_3\erp_documents\PO 202540R MO Denman Island Tea Co.pdf"
try:
    reader = PdfReader(pdf_path)
    print(f"Number of pages: {len(reader.pages)}")
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    print("--- PDF Content Start ---")
    print(text)
    print("--- PDF Content End ---")
except Exception as e:
    print(f"Error reading PDF: {e}")
