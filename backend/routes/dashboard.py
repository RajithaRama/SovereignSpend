from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from backend.database import get_db
from backend.models import Account, Transaction
from backend.schemas import DashboardSummary, CategoryBreakdown, TimeseriesPoint, AccountOverview
from typing import List
from datetime import datetime, timedelta
from collections import defaultdict

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get overall financial summary across all accounts"""
    # Total balance across all accounts
    total_balance = db.query(func.sum(Account.balance)).scalar() or 0.0
    
    # Monthly income and expenses (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    monthly_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "income",
        Transaction.date >= thirty_days_ago
    ).scalar() or 0.0
    
    monthly_expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "expense",
        Transaction.date >= thirty_days_ago
    ).scalar() or 0.0
    
    account_count = db.query(func.count(Account.id)).scalar()
    
    return DashboardSummary(
        total_balance=round(total_balance, 2),
        monthly_income=round(monthly_income, 2),
        monthly_expenses=round(monthly_expenses, 2),
        account_count=account_count
    )

@router.get("/categories", response_model=List[CategoryBreakdown])
def get_category_breakdown(
    month: int = None, 
    year: int = None, 
    db: Session = Depends(get_db)
):
    """Get spending breakdown by category"""
    
    query = db.query(
        Transaction.category,
        func.sum(Transaction.amount).label("total")
    ).filter(
        Transaction.type == "expense",
        Transaction.category.isnot(None)
    )

    if month and year:
        # Filter by specific month and year
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        query = query.filter(
            Transaction.date >= start_date,
            Transaction.date < end_date
        )
    else:
        # Default to last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        query = query.filter(Transaction.date >= thirty_days_ago)
        
    category_totals = query.group_by(Transaction.category).all()
    
    total_expenses = sum(cat[1] for cat in category_totals)
    
    breakdown = []
    for category, amount in category_totals:
        percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
        breakdown.append(CategoryBreakdown(
            category=category,
            amount=round(amount, 2),
            percentage=round(percentage, 2)
        ))
    
    return sorted(breakdown, key=lambda x: x.amount, reverse=True)

@router.get("/timeseries", response_model=List[TimeseriesPoint])
def get_timeseries_data(db: Session = Depends(get_db)):
    """Get timeseries data for savings, earnings, and expenditure"""
    # Get last 12 months of data
    twelve_months_ago = datetime.now() - timedelta(days=365)
    
    # Get all transactions in the period
    transactions = db.query(Transaction).filter(
        Transaction.date >= twelve_months_ago
    ).all()
    
    # Group by month
    monthly_data = defaultdict(lambda: {"earnings": 0.0, "expenditure": 0.0})
    
    for trans in transactions:
        month_key = trans.date.strftime("%Y-%m")
        if trans.type == "income":
            monthly_data[month_key]["earnings"] += trans.amount
        else:
            monthly_data[month_key]["expenditure"] += trans.amount
    
    # Calculate cumulative savings
    timeseries = []
    cumulative_savings = 0.0
    
    # Sort by date
    sorted_months = sorted(monthly_data.keys())
    
    for month in sorted_months:
        data = monthly_data[month]
        monthly_savings = data["earnings"] - data["expenditure"]
        cumulative_savings += monthly_savings
        
        timeseries.append(TimeseriesPoint(
            date=month,
            savings=round(cumulative_savings, 2),
            earnings=round(data["earnings"], 2),
            expenditure=round(data["expenditure"], 2)
        ))
    
    return timeseries

@router.get("/category-timeseries")
def get_category_timeseries(db: Session = Depends(get_db)):
    """Get spending timeseries by category"""
    # Get last 12 months of data
    twelve_months_ago = datetime.now() - timedelta(days=365)
    
    transactions = db.query(Transaction).filter(
        Transaction.type == "expense",
        Transaction.date >= twelve_months_ago,
        Transaction.category.isnot(None)
    ).all()
    
    # Structure: { "2023-01": { "Food": 100, "Rent": 500 }, ... }
    monthly_data = defaultdict(lambda: defaultdict(float))
    all_categories = set()
    
    for trans in transactions:
        month_key = trans.date.strftime("%Y-%m")
        monthly_data[month_key][trans.category] += trans.amount
        all_categories.add(trans.category)
        
    # Format for chart
    result = []
    sorted_months = sorted(monthly_data.keys())
    
    for month in sorted_months:
        month_entry = {"date": month}
        for category in all_categories:
            month_entry[category] = round(monthly_data[month][category], 2)
        result.append(month_entry)
        
    return result

@router.get("/accounts-overview", response_model=List[AccountOverview])
def get_accounts_overview(db: Session = Depends(get_db)):
    """Get per-account balances and recent activity"""
    accounts = db.query(Account).all()
    
    overview = []
    for account in accounts:
        # Get last 5 transactions for this account
        recent_transactions = db.query(Transaction).filter(
            Transaction.account_id == account.id
        ).order_by(Transaction.date.desc()).limit(5).all()
        
        # Calculate monthly change (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        monthly_income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "income",
            Transaction.date >= thirty_days_ago
        ).scalar() or 0.0
        
        monthly_expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "expense",
            Transaction.date >= thirty_days_ago
        ).scalar() or 0.0
        
        monthly_change = monthly_income - monthly_expenses
        
        overview.append(AccountOverview(
            account=account,
            recent_transactions=recent_transactions,
            monthly_change=round(monthly_change, 2)
        ))
    
    return overview

@router.get("/recent")
def get_recent_transactions(db: Session = Depends(get_db)):
    """Get recent transactions across all accounts"""
    transactions = db.query(Transaction).order_by(
        Transaction.date.desc()
    ).limit(10).all()
    
    return transactions
