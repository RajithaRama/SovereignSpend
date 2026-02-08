from backend.database import SessionLocal
from backend.models import Account

def list_accounts():
    db = SessionLocal()
    try:
        accounts = db.query(Account).all()
        if not accounts:
            print("No accounts found.")
        for acc in accounts:
            print(f"ID: {acc.id} | Name: {acc.name} | Balance: {acc.balance}")
    finally:
        db.close()

if __name__ == "__main__":
    list_accounts()
