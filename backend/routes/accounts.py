from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Account
from backend.schemas import AccountCreate, AccountUpdate, Account as AccountSchema
from typing import List

router = APIRouter(prefix="/api/accounts", tags=["accounts"])

@router.get("/", response_model=List[AccountSchema])
def list_accounts(db: Session = Depends(get_db)):
    """List all accounts with current balances"""
    accounts = db.query(Account).all()
    return accounts

@router.post("/", response_model=AccountSchema)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account"""
    # Check if account with same name exists
    existing = db.query(Account).filter(Account.name == account.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account with this name already exists")
    
    db_account = Account(**account.model_dump())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@router.put("/{account_id}", response_model=AccountSchema)
def update_account(account_id: int, account: AccountUpdate, db: Session = Depends(get_db)):
    """Update an account"""
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = account.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account

@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Delete an account"""
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    db.delete(db_account)
    db.commit()
    return {"message": "Account deleted successfully"}
