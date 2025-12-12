# This file imports data from a excel workbook into the existing customers table via pandas
import pandas as pd
from sqlalchemy.orm import Session
from database import engine
from models import Customer

existing_customers_file = 'archive\existing_customer_details_11292025.xlsx'
df = pd.read_excel(existing_customers_file)

session = Session(bind=engine)

# add the data from df to customers table