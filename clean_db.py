import os
import sys
from sqlalchemy import create_engine, MetaData

# Ensure we can import from backend
sys.path.append(os.getcwd())

from backend.database import DATABASE_PATH, Base, engine

def clean_db():
    print(f"Cleaning database at {DATABASE_PATH}...")
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped.")
    
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    print("All tables recreated.")

if __name__ == "__main__":
    confirmation = input("This will delete all data. Are you sure? (y/n): ")
    if confirmation.lower() == 'y':
        clean_db()
    else:
        print("Operation cancelled.")
