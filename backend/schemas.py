from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# Account Schemas
class AccountBase(BaseModel):
    name: str

class AccountCreate(AccountBase):
    balance: float = 0.0

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    balance: Optional[float] = None

class Account(AccountBase):
    id: int
    balance: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionBase(BaseModel):
    amount: float
    type: str  # "income" or "expense"
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

class TransactionCreate(TransactionBase):
    account_id: int

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

class Transaction(TransactionBase):
    id: int
    account_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Transfer Schemas
class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float
    description: Optional[str] = None
    date: Optional[datetime] = None

class Transfer(BaseModel):
    id: int
    from_account_id: int
    to_account_id: int
    amount: float
    description: Optional[str]
    date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# Invoice Schemas
class InvoiceUploadResponse(BaseModel):
    id: int
    filename: str
    extracted_text: Optional[str]
    uploaded_at: datetime

# Dashboard Schemas
class DashboardSummary(BaseModel):
    total_balance: float
    monthly_income: float
    monthly_expenses: float
    account_count: int

class CategoryBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float

class TimeseriesPoint(BaseModel):
    date: str
    savings: float
    earnings: float
    expenditure: float

class AccountOverview(BaseModel):
    account: Account
    recent_transactions: List[Transaction]
    monthly_change: float
