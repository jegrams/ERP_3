# in main.py (or a separate init_db.py)
from database import Base, engine
from models import User

Base.metadata.create_all(bind=engine)

# display a list of all users in the users table
from sqlalchemy.orm import Session
# from database import SessionLocal

# function to add a new user
def add_user(name: str, email: str, session: Session):
    new_user = User(name=name, email=email)
    session.add(new_user)

# add_user("Alice", "alice@example.com")

session = Session(bind=engine)

add_user("Jack", "jack@example.com", session)

session.commit()

session.close()