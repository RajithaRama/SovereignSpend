from backend.models import Account, Transaction
from datetime import datetime

def test_create_account(db_session):
    account = Account(name="Test Account", balance=1000.0)
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    
    assert account.id is not None
    assert account.name == "Test Account"
    assert account.balance == 1000.0

def test_create_transaction(db_session):
    account = Account(name="Main Account", balance=1000.0)
    db_session.add(account)
    db_session.commit()
    
    transaction = Transaction(
        account_id=account.id,
        date=datetime.now(),
        description="Test Purchase",
        amount=-50.0,
        type="expense",
        category="Shopping"
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    assert transaction.id is not None
    assert transaction.amount == -50.0
    assert transaction.account.name == "Main Account"

def test_account_balance_update(db_session):
    account = Account(name="Savings", balance=500.0)
    db_session.add(account)
    db_session.commit()
    
    account.balance += 100.0
    db_session.commit()
    db_session.refresh(account)
    
    assert account.balance == 600.0
