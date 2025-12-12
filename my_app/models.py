# models.py
from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    contact_name = Column(String, nullable=True)
    ship_to_phone = Column(String, nullable=True)
    email_address = Column(String, unique=True, nullable=True)
    ship_to_addr1 = Column(String, nullable=True)
    ship_to_addr2 = Column(String, nullable=True)
    ship_to_city = Column(String, nullable=True)
    ship_to_state = Column(String, nullable=True)
    ship_to_zip = Column(String, nullable=True)
    ship_to_country = Column(String, nullable=True)
    email_name = Column(String, nullable=True)

    def __repr__(self):
        return f'{self.customer_name}'