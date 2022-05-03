#File To Actually Create The Database 
#Run This File To Create The Database In The Heroku Console
from app import db, User, Pixel

db.create_all()
try:
  Pixel.__table__.create(db.session.bind)
  User.__table__.create(db.session.bind)
except Exception:
  print("Already Exist")