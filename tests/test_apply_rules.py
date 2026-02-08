import os
os.environ["DB_ENV"] = "testing"

# Delete test DB if exists
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
from datetime import datetime

# Initialize test DB
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_apply_rules_idempotency():
    print("Running Apply Rules Idempotency Test...")
    
    with SessionLocal() as db:
        from backend.models import Account, Transaction
        
        # 1. Setup Accounts
        aib = Account(id=1, name="AIB Checking", balance=1000.0)
        boi = Account(id=2, name="BOI Savings", balance=0.0)
        db.add(aib)
        db.add(boi)
        db.commit()
        
        # 2. Reload Rules (assumes rules.json exists with the BOI rule)
        # Note: config_loader loads from rules.json. 
        # Make sure rules.json has the expected rule or insert it manually here.
        load_rules(db)
        
        # Verify rule exists
        from backend.models import TransactionRule
        rule = db.query(TransactionRule).first()
        if not rule:
            print("[Setup] No rules found! Creating manual rule for test.")
            rule = TransactionRule(
                match_pattern="D/D BOI Savings DS",
                origin_type="expense",
                rule_type="link_account",
                target_account_id=2,
                target_type="income"
            )
            db.add(rule)
            db.commit()
            
        # 3. Create Source Transaction
        # "D/D BOI Savings DS" expense in AIB
        trans = Transaction(
            account_id=1,
            amount=100.0,
            type="expense",
            category="Transfer",
            description="D/D BOI Savings DS - Manual Test",
            date=datetime.now()
        )
        db.add(trans)
        db.commit()
        print(f"[Setup] Created source transaction: {trans.description}")

    # 4. Run Apply Rules (First Pass)
    print("[Action] Applying rules (Pass 1)...")
    response = client.post("/api/transactions/apply-rules")
    print(f"[Result] Pass 1 Response: {response.json()}")
    
    assert response.status_code == 200
    res_json = response.json()
    assert res_json['created'] == 1, f"Expected 1 created, got {res_json['created']}"
    
    # 5. Verify Linked Transaction Exists
    with SessionLocal() as db:
        from backend.models import Transaction
        linked = db.query(Transaction).filter(
            Transaction.account_id == 2,
            Transaction.amount == 100.0,
            Transaction.type == "income"
        ).all()
        assert len(linked) == 1, f"Expected 1 linked transaction, found {len(linked)}"
        print("[Verify] Linked transaction found.")

    # 6. Run Apply Rules (Second Pass - Idempotency Check)
    print("[Action] Applying rules (Pass 2)...")
    response = client.post("/api/transactions/apply-rules")
    print(f"[Result] Pass 2 Response: {response.json()}")
    
    assert response.status_code == 200
    res_json = response.json()
    assert res_json['created'] == 0, f"Expected 0 created (duplicate), got {res_json['created']}"
    
    # 7. Verify NO extra transaction
    with SessionLocal() as db:
        from backend.models import Transaction
        linked = db.query(Transaction).filter(
            Transaction.account_id == 2,
            Transaction.amount == 100.0,
            Transaction.type == "income"
        ).all()
        assert len(linked) == 1, f"Expected 1 linked transaction, found {len(linked)}"
        print("[Verify] Still only 1 linked transaction. SUCCESS.")

if __name__ == "__main__":
    test_apply_rules_idempotency()
