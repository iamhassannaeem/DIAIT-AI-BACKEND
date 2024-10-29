from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker


# Connection URL
db_url = "postgresql://postgres:1234@localhost/Dialit_db"

# Create an engine
engine = create_engine(db_url)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Reflect existing tables
metadata = MetaData()
metadata.reflect(bind=engine)

# List all tables
print("Tables in the database:")
for table in metadata.tables:
    print(table)
