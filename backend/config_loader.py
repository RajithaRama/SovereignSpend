import json
import os
from sqlalchemy.orm import Session
from backend.models import TransactionRule, Account
from backend.database import SessionLocal

def load_rules(db: Session = None):
    """Load matching rules from rules.json into the database"""
    rules_path = os.getenv("RULES_FILE", "rules.json")
    
    if not os.path.exists(rules_path):
        print(f"[INFO] No rules file found at {rules_path}")
        return

    print(f"[INFO] Loading rules from {rules_path}")
    
    try:
        with open(rules_path, 'r') as f:
            rules_data = json.load(f)
            
        own_db = False
        if db is None:
            db = SessionLocal()
            own_db = True
            
        try:
            # Clear existing rules? 
            # Ideally we might want to sync them, but for now let's just ensure they exist or replace them.
            # Strategy: Simple "Upsert" based on match_pattern + rule_type uniqueness?
            # Or simpler: Delete all and re-insert (easiest for config file source of truth)
            
            db.query(TransactionRule).delete()
            
            for rule_def in rules_data:
                # Resolve account name to ID
                target_account_id = None
                if target_account_name := rule_def.get("target_account_name"):
                    account = db.query(Account).filter(Account.name == target_account_name).first()
                    if account:
                        target_account_id = account.id
                    else:
                        print(f"[WARN] Target account '{target_account_name}' not found for rule '{rule_def.get('match_pattern')}'")
                        continue
                
                rule = TransactionRule(
                    match_pattern=rule_def["match_pattern"],
                    match_type=rule_def.get("match_type", "contains"),
                    origin_type=rule_def.get("origin_type"),
                    rule_type=rule_def["rule_type"],
                    target_account_id=target_account_id,
                    target_type=rule_def.get("target_type"),
                    category=rule_def.get("category")
                )
                db.add(rule)
            
            db.commit()
            print(f"[INFO] Loaded {len(rules_data)} rules")
            
        finally:
            if own_db:
                db.close()
                
    except Exception as e:
        print(f"[ERROR] Failed to load rules: {e}")
