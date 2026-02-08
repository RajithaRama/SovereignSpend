import os
# Set environment to testing BEFORE importing anything from backend
os.environ["DB_ENV"] = "testing"

# Delete test DB if exists (must do before importing backend which opens connection)
if os.path.exists("./finance_tracker_test.db"):
    try:
        os.remove("./finance_tracker_test.db")
        print("[Setup] Deleted existing test database.")
    except Exception as e:
        print(f"[Setup] Warning: Could not delete test database: {e}")

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db, init_db, SessionLocal, engine
from backend.models import Base
from backend.config_loader import load_rules
import io

# Initialize test DB
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_rule_execution():
    print("Running tests against TEST DATABASE...")
    
    # 1. Setup: Ensure we have clean slate or specific state
    # For now, let's just make sure we have the accounts
    # We might need to seed them if it's a fresh test DB
    
    with SessionLocal() as db:
        from backend.models import Account
        # Ensure accounts exist
        aib = db.query(Account).filter(Account.id == 1).first()
        if not aib:
            db.add(Account(id=1, name="AIB Checking", balance=1000.0))
        
        boi = db.query(Account).filter(Account.id == 2).first()
        if not boi:
            db.add(Account(id=2, name="BOI Savings", balance=0.0))
        
        db.commit()

    # Reload rules NOW that accounts exist
    load_rules()
    
    with SessionLocal() as db:
        rules = db.query(load_rules.__globals__['TransactionRule']).all()
        print(f"[Verify] Rules in DB before upload: {len(rules)}")
        for r in rules:
             print(f" - {r.match_pattern} -> {r.target_account_id}")

    # 2. Upload CSV to Account 1 (AIB Checking)
    csv_content = (
        "Posted Transactions Date,Description,Debit Amount,Credit Amount\n"
        "01/02/26,D/D BOI Savings DS Test Client,102.00,,\n"
    )
    
    file_obj = io.BytesIO(csv_content.encode('utf-8'))
    files = {
        'file': ('test_statement.csv', file_obj, 'text/csv')
    }
    data = {
        'account_id': 1,
        'force': 'true'
    }
    
    print("Uploading CSV...")
    response = client.post("/api/upload/bank-statement", files=files, data=data)
    
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return
        
    print(f"Upload successful: {response.json()}")
    
    # 3. Verify Transactions
    resp_trans = client.get("/api/transactions/?account_id=2")
    if resp_trans.status_code == 200:
        transactions = resp_trans.json()
        found = False
        for t in transactions:
            print(f"Checking: {t['description']} - {t['amount']}")
            if "D/D BOI Savings DS" in t['description'] and t['amount'] == 102.0 and t['type'] == 'income':
                found = True
                print("SUCCESS: Found linked Income transaction in BOI Savings (TEST DB)!")
                break
        
        if not found:
            print("FAILURE: Did not find linked transaction.")
            print("Transactions:", transactions)
    else:
        print(f"Failed to fetch transactions: {resp_trans.text}")

if __name__ == "__main__":
    try:
        test_rule_execution()
    finally:
        # Cleanup (optional, or rely on it being a throwaway db)
        pass
