from sqlalchemy.orm import sessionmaker
from models import get_engine, OurCompany

def update_company_info():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if company info exists
        company = session.query(OurCompany).first()

        if not company:
            company = OurCompany()
            session.add(company)
            print("Creating new company record.")
        else:
            print("Updating existing company record.")

        # Update fields
        company.company_name = 'Arete Imports, LLC'
        company.address1 = '3237 Minnesota Ave'
        company.address2 = None
        company.city = 'Costa Mesa'
        company.state = 'CA'
        company.zip_code = '92626'
        company.country = 'USA'
        company.phone = '+1-949-216-0460'
        company.email = 'jegrams@mana-organics.com'
        company.website = 'https://www.manaorganics-usa.com/'
        company.IRS_Emp_ID = '47-5101193'
        company.CA_Sec_ID = '201523010050'
        company.BOE_sales_lic_num = 'EA 102-917721'

        session.commit()
        
        # Verify
        updated_company = session.query(OurCompany).first()
        print("\nUpdated Company Info:")
        print(f"Name: {updated_company.company_name}")
        print(f"Address: {updated_company.address1}, {updated_company.city}, {updated_company.state} {updated_company.zip_code}")
        print(f"Phone: {updated_company.phone}")
        print(f"Email: {updated_company.email}")
        print(f"Website: {updated_company.website}")
        print(f"IRS ID: {updated_company.IRS_Emp_ID}")

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    update_company_info()
