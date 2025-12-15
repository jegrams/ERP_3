
import openpyxl
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.utils import get_column_letter

def update_named_ranges():
    file_path = r'c:\Users\jegra\MyPython\ERP_3\assets\other\invoice_template.xlsx'
    
    try:
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active # Assuming the ranges are on the active sheet
        sheet_title = sheet.title
        print(f"Loaded workbook. Active sheet: {sheet_title}")

        # Rows 16 to 24
        start_row = 16
        end_row = 24
        
        # Columns mappings
        # B: Quantity_{i}
        # C: Unit_{i}
        # D: Desc_{i}
        # E: Unit_price_{i}
        # F: Amount_{i}
        
        col_map = {
            'B': 'Quantity',
            'C': 'Unit',
            'D': 'Desc',
            'E': 'Unit_price',
            'F': 'Amount'
        }

        # Handling "Unit _2" vs "Unit_2" - User request had some inconsistencies:
        # "Unit_1, Unit _2, Unit _3"
        # "Desc_1, Desc _2, Desc _3"
        # "Unit_price_1, Unit_price _2, Unit_price _3"
        # "Amount_1, Amount _2, Amount _3"
        # Quantity seems consistent "Quantity_1, Quantity_2"
        # The user seems to have a space in the request for 2 and 3, but likely wants a consistent format.
        # "Unit_1" (no space) but "Unit _2" (space).
        # Standard convention is usually underscore without space for variable-like names.
        # However, Excel names CANNOT contain spaces. So "Unit _2" is invalid invalid Excel name.
        # I will assume the user made a typo and wants "Unit_2", "Desc_2", etc.
        # I will use standard underscore format: Name_{i}
        
        count = 1
        for row in range(start_row, end_row + 1):
            for col_letter, name_prefix in col_map.items():
                name = f"{name_prefix}_{count}"
                # content of range
                # DefinedName requires absolute reference usually, e.g. Sheet1!$B$16
                reference = f"'{sheet_title}'!${col_letter}${row}"
                
                # Check if exists and replace, or just create new
                if name in wb.defined_names:
                    del wb.defined_names[name]
                
                d = DefinedName(name, attr_text=reference)
                wb.defined_names.append(d)
                print(f"Defined {name} referring to {reference}")
            
            count += 1

        wb.save(file_path)
        print(" Workbook saved successfully.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_named_ranges()
