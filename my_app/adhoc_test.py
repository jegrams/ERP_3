from database import engine
from models import User

from sqlalchemy.orm import Session

session = Session(bind=engine)

users = session.query(User).all()

for user in users:
    print(user.id, user.name, user.email)

session.close()