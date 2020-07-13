from . import db

db.build()

version = db.get_db_version()
db.upgrade(version)
