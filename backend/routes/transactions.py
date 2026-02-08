from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Transaction, Transfer, Account
from backend.schemas import (
    TransactionCreate, TransactionUpdate, Transaction as TransactionSchema,
    TransferCreate, Transfer as TransferSchema
)
from backend.ollama_service import ollama_service
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.get("/", response_model=List[TransactionSchema])
def list_transactions(
    account_id: Optional[int] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all transactions with optional filtering"""
    query = db.query(Transaction)
    
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if category:
        query = query.filter(Transaction.category == category)
    if start_date:
        query = query.filter(Transaction.date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Transaction.date <= datetime.fromisoformat(end_date))
    
    transactions = query.order_by(Transaction.date.desc()).all()
    return transactions

@router.post("/check-duplicates", response_model=List[TransactionSchema])
def check_duplicates(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """Check for potential duplicate transactions"""
    # Parse the date from the request to ensure we compare dates correctly
    # The transaction.date coming in might be a datetime
    
    # We look for transactions with same amount, description (case-insensitive) and same date
    # We'll allow a small window for date? No, strict date for now as per plan.
    
    target_date = transaction.date.date() if transaction.date else datetime.now().date()
    
    query = db.query(Transaction).filter(
        Transaction.amount == transaction.amount,
        Transaction.description.ilike(transaction.description) # Case-insensitive
    )
    
    # Filter by date only (ignoring time) requires some sqlalchemy magic or range
    # easier to just filter >= date start and < date end
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    
    query = query.filter(Transaction.date >= start_of_day, Transaction.date <= end_of_day)
    
    if transaction.account_id:
        query = query.filter(Transaction.account_id == transaction.account_id)
        
    return query.all()

@router.post("/", response_model=TransactionSchema)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    """Create a new transaction with automated AI category classification"""
    # Verify account exists
    account = db.query(Account).filter(Account.id == transaction.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Auto-classify if category not provided
    if not transaction.category and transaction.description:
        transaction.category = ollama_service.classify_transaction(
            transaction.description, 
            transaction.amount
        )
    
    # Create transaction
    db_transaction = Transaction(**transaction.model_dump())
    db.add(db_transaction)
    
    # Update account balance
    if transaction.type == "income":
        account.balance += transaction.amount
    else:  # expense
        account.balance -= transaction.amount
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.post("/transfer", response_model=TransferSchema)
def create_transfer(transfer: TransferCreate, db: Session = Depends(get_db)):
    """Create a transfer between accounts"""
    # Verify both accounts exist
    from_account = db.query(Account).filter(Account.id == transfer.from_account_id).first()
    to_account = db.query(Account).filter(Account.id == transfer.to_account_id).first()
    
    if not from_account or not to_account:
        raise HTTPException(status_code=404, detail="One or both accounts not found")
    
    if from_account.id == to_account.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")
    
    # Check sufficient balance
    if from_account.balance < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Create transfer record
    db_transfer = Transfer(**transfer.model_dump())
    db.add(db_transfer)
    
    # Update balances
    from_account.balance -= transfer.amount
    to_account.balance += transfer.amount
    
    db.commit()
    db.refresh(db_transfer)
    return db_transfer

@router.put("/{transaction_id}", response_model=TransactionSchema)
def update_transaction(
    transaction_id: int, 
    transaction: TransactionUpdate, 
    db: Session = Depends(get_db)
):
    """Update a transaction"""
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # If amount or type changes, need to update account balance
    account = db.query(Account).filter(Account.id == db_transaction.account_id).first()
    
    # Revert old transaction
    if db_transaction.type == "income":
        account.balance -= db_transaction.amount
    else:
        account.balance += db_transaction.amount
    
    # Update transaction
    update_data = transaction.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_transaction, field, value)
    
    # Apply new transaction
    if db_transaction.type == "income":
        account.balance += db_transaction.amount
    else:
        account.balance -= db_transaction.amount
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Delete a transaction"""
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Revert account balance
    account = db.query(Account).filter(Account.id == db_transaction.account_id).first()
    if db_transaction.type == "income":
        account.balance -= db_transaction.amount
    else:
        account.balance += db_transaction.amount
    
    db.delete(db_transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}

@router.post("/apply-rules")
def apply_rules_to_all_transactions(db: Session = Depends(get_db)):
    """Apply all transaction rules to existing transactions"""
    from backend.services.rules_engine import RulesEngine
    engine = RulesEngine(db)
    result = engine.apply_rules_to_all()
    return result

@router.post("/import-foreign")
def import_foreign_transactions(
    account_id: int,
    transactions: List[dict],
    db: Session = Depends(get_db)
):
    """Import user-verified foreign currency transactions
    
    Expects transactions to have been converted to EUR by the user.
    Each transaction should have: date, description, amount (in EUR)
    """
    # Verify account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    created_count = 0
    errors = []
    
    for trans_data in transactions:
        try:
            # Validate required fields
            if not all(key in trans_data for key in ['date', 'description', 'amount']):
                errors.append(f"Missing required fields in transaction: {trans_data}")
                continue
            
            amount = float(trans_data['amount'])
            
            # Skip zero amount transactions
            if amount == 0:
                continue
            
            # Determine type based on amount sign
            is_expense = amount < 0
            abs_amount = abs(amount)
            trans_type = "expense" if is_expense else "income"
            
            # Parse date
            date_str = trans_data['date']
            try:
                trans_date = datetime.fromisoformat(date_str)
            except:
                try:
                    trans_date = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    errors.append(f"Invalid date format for transaction: {trans_data}")
                    continue
            
            description = trans_data.get('description', 'Foreign transaction')
            
            # Check for duplicates
            start_of_day = datetime.combine(trans_date.date(), datetime.min.time())
            end_of_day = datetime.combine(trans_date.date(), datetime.max.time())
            
            existing = db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.amount == abs_amount,
                Transaction.type == trans_type,
                Transaction.description.ilike(description),
                Transaction.date >= start_of_day,
                Transaction.date <= end_of_day
            ).first()
            
            if existing:
                errors.append(f"Duplicate transaction found: {description} on {date_str}")
                continue
            
            # Classify transaction
            category = ollama_service.classify_transaction(description, abs_amount)
            
            # Create transaction
            transaction = Transaction(
                account_id=account_id,
                amount=abs_amount,
                type=trans_type,
                category=category,
                description=description,
                date=trans_date
            )
            db.add(transaction)
            
            # Update account balance
            if trans_type == "income":
                account.balance += abs_amount
            else:
                account.balance -= abs_amount
            
            # Apply Transaction Rules
            from backend.services.rules_engine import RulesEngine
            engine = RulesEngine(db)
            engine.apply_rules(transaction)
            
            created_count += 1
            
        except Exception as e:
            errors.append(f"Error processing transaction {trans_data}: {str(e)}")
            continue
    
    db.commit()
    
    return {
        "message": f"Imported {created_count} foreign transactions",
        "transactions_created": created_count,
        "errors": errors
    }
