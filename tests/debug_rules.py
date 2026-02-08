import os
os.environ["DB_ENV"] = "testing"

from backend.database import SessionLocal
from backend.models import TransactionRule

print(f"Using database: {os.getenv('DB_ENV')}")

db = SessionLocal()
rules = db.query(TransactionRule).all()
print(f"Found {len(rules)} rules in TEST DB:")
for r in rules:
    print(f"Rule: pattern='{r.match_pattern}', type='{r.rule_type}', target_id={r.target_account_id}, origin='{r.origin_type}'")
db.close()
