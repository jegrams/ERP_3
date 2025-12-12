import pandas as pd

file_path = r"C:\Users\jegra\MyPython\ERP_3\my_app\archive\existing_customer_details_11292025.xlsx"
try:
    df = pd.read_excel(file_path)
    print("Columns found:")
    for col in df.columns:
        print(f"- {col}")
    print("\nFirst row sample:")
    print(df.iloc[0].to_dict())
except Exception as e:
    print(f"Error reading file: {e}")
