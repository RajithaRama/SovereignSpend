from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    transfers_from = relationship("Transfer", foreign_keys="Transfer.from_account_id", back_populates="from_account")
    transfers_to = relationship("Transfer", foreign_keys="Transfer.to_account_id", back_populates="to_account")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # "income" or "expense"
    category = Column(String, nullable=True)
    description = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")

class Transfer(Base):
    __tablename__ = "transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="transfers_from")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="transfers_to")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    extracted_text = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    file_hash = Column(String, nullable=True, index=True)

class BankStatement(Base):
    __tablename__ = "bank_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    parsed_status = Column(String, default="pending")  # pending, processing, completed, failed
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    file_hash = Column(String, nullable=True, index=True)

class TransactionRule(Base):
    __tablename__ = "transaction_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    match_pattern = Column(String, nullable=False)
    match_type = Column(String, default="contains")
    origin_type = Column(String, nullable=True)  # "income" or "expense"
    rule_type = Column(String, nullable=False)   # "link_account", "update_category"
    
    # Context for link_account
    target_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    target_type = Column(String, nullable=True)  # "income" or "expense"
    
    # Context for update_category
    category = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    target_account = relationship("Account")
