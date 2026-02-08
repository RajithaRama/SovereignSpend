from sqlalchemy.orm import Session
from backend.models import Transaction, TransactionRule, Account
from datetime import datetime

class RulesEngine:
    def __init__(self, db: Session):
        self.db = db
        # Cache rules? For now, fetch on init or per call. 
        # Per call is safer for long running processes if rules change, but slower.
        # Let's fetch once per engine instance if short-lived.
        self.rules = self.db.query(TransactionRule).all()

    def apply_rules(self, transaction: Transaction) -> list[Transaction]:
        """
        Apply all matching rules to a single transaction.
        Returns a list of newly created transactions (linked).
        """
        created_transactions = []
        
        # Determine strict transaction type
        # transaction.type is "income" or "expense"
        trans_type = transaction.type
        description = transaction.description or ""
        abs_amount = transaction.amount # Stored as positive

        for rule in self.rules:
            # 1. Match Pattern
            is_match = False
            if rule.match_type == "contains":
                if rule.match_pattern.lower() in description.lower():
                    is_match = True
            elif rule.match_type == "exact":
                 if rule.match_pattern.lower() == description.lower():
                    is_match = True
            
            if not is_match:
                continue

            # 2. Match Origin Type
            if rule.origin_type:
                if rule.origin_type.lower() != trans_type.lower():
                    continue

            # 3. Execute Rule
            print(f"[RulesEngine] Match found: {rule.match_pattern} for '{description}'")
            
            if rule.rule_type == "link_account" and rule.target_account_id:
                # Prevent matching itself or circular logic if needed
                if rule.target_account_id == transaction.account_id:
                    continue

                link_type = rule.target_type or "income"
                link_amount = abs_amount
                
                # Check for DUPLICATE in target account
                # Criteria: Same Target Account, Same Date, Same Amount, Same Description
                if self._is_duplicate(rule.target_account_id, transaction.date, link_amount, description, link_type):
                    print(f"[RulesEngine] Skipping duplicate creation for rule '{rule.match_pattern}'")
                    continue
                
                # Create Linked Transaction
                linked_trans = Transaction(
                    account_id=rule.target_account_id,
                    amount=link_amount,
                    type=link_type,
                    category=rule.category or "Transfer", # Default or from rule
                    description=description,
                    date=transaction.date
                )
                self.db.add(linked_trans)
                
                # Update Balance
                target_acc = self.db.query(Account).get(rule.target_account_id)
                if target_acc:
                    if link_type == "income":
                        target_acc.balance += link_amount
                    else:
                        target_acc.balance -= link_amount
                
                created_transactions.append(linked_trans)
                print(f"[RulesEngine] Created linked transaction in account {rule.target_account_id}")

            elif rule.rule_type == "update_category":
                # Only update if category is different
                if rule.category and transaction.category != rule.category:
                    transaction.category = rule.category
                    # No new transaction created, just updated existing
                    print(f"[RulesEngine] Updated category to '{rule.category}'")

        return created_transactions

    def _is_duplicate(self, account_id: int, date: datetime, amount: float, description: str, type_: str) -> bool:
        """
        Check if a transaction with these exact details already exists.
        """
        # Strict Date Check
        existing = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.date == date,
            Transaction.amount == amount,
            Transaction.type == type_,
            Transaction.description == description
        ).first()
        return existing is not None

    def apply_rules_to_all(self) -> dict:
        """
        Apply rules to ALL transactions in the database.
        Returns check stats.
        """
        all_transactions = self.db.query(Transaction).all()
        total_created = 0
        
        for trans in all_transactions:
            new_trans = self.apply_rules(trans)
            total_created += len(new_trans)
            
        self.db.commit()
        return {"processed": len(all_transactions), "created": total_created}
