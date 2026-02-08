import pytest
from datetime import datetime

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

# Account Tests
def test_create_account_api(client):
    """Test account creation"""
    account_data = {
        "name": "API Test Account",
        "balance": 500.0
    }
    response = client.post("/api/accounts/", json=account_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "API Test Account"
    assert data["balance"] == 500.0
    assert "id" in data

def test_create_duplicate_account(client):
    """Test that duplicate account names are rejected"""
    account_data = {"name": "Duplicate Test", "balance": 100}
    
    # Create first account
    response1 = client.post("/api/accounts/", json=account_data)
    assert response1.status_code == 200
    
    # Try to create duplicate
    response2 = client.post("/api/accounts/", json=account_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"].lower()

def test_get_accounts_api(client):
    """Test listing accounts"""
    client.post("/api/accounts/", json={"name": "Acc 1", "balance": 100})
    client.post("/api/accounts/", json={"name": "Acc 2", "balance": 200})
    
    response = client.get("/api/accounts/")
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) >= 2

def test_update_account(client):
    """Test account update"""
    # Create account
    acc_resp = client.post("/api/accounts/", json={"name": "Update Test", "balance": 100})
    account_id = acc_resp.json()["id"]
    
    # Update account
    update_data = {"name": "Updated Name", "balance": 200}
    response = client.put(f"/api/accounts/{account_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert response.json()["balance"] == 200

def test_update_nonexistent_account(client):
    """Test updating non-existent account returns 404"""
    response = client.put("/api/accounts/99999", json={"name": "Test"})
    assert response.status_code == 404

def test_delete_account(client):
    """Test account deletion"""
    # Create account
    acc_resp = client.post("/api/accounts/", json={"name": "Delete Test", "balance": 100})
    account_id = acc_resp.json()["id"]
    
    # Delete account
    response = client.delete(f"/api/accounts/{account_id}")
    assert response.status_code == 200
    
    # Verify account is deleted
    get_response = client.get("/api/accounts/")
    accounts = get_response.json()
    assert not any(acc["id"] == account_id for acc in accounts)

# Transaction Tests
def test_create_transaction_api(client):
    """Test transaction creation"""
    # Create account first
    acc_resp = client.post("/api/accounts/", json={"name": "Trans Acc", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    transaction_data = {
        "account_id": account_id,
        "date": datetime.now().isoformat(),
        "description": "Starbucks",
        "amount": -5.50,
        "type": "expense",
        "category": "Food & Dining"
    }
    response = client.post("/api/transactions/", json=transaction_data)
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Starbucks"
    assert data["amount"] == -5.50

def test_create_transaction_updates_balance(client):
    """Test that creating a transaction updates account balance"""
    # Create account
    acc_resp = client.post("/api/accounts/", json={"name": "Balance Test", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    # Create expense transaction
    client.post("/api/transactions/", json={
        "account_id": account_id,
        "date": datetime.now().isoformat(),
        "description": "Purchase",
        "amount": 100.0,
        "type": "expense",
        "category": "Shopping"
    })
    
    # Check balance decreased
    acc_response = client.get("/api/accounts/")
    account = next(acc for acc in acc_response.json() if acc["id"] == account_id)
    assert account["balance"] == 900.0  # 1000 - 100

def test_create_transaction_invalid_account(client):
    """Test creating transaction for non-existent account returns 404"""
    transaction_data = {
        "account_id": 99999,
        "date": datetime.now().isoformat(),
        "description": "Test",
        "amount": 10.0,
        "type": "income",
        "category": "Other"
    }
    response = client.post("/api/transactions/", json=transaction_data)
    assert response.status_code == 404

def test_get_transactions_with_filters(client):
    """Test transaction listing with filters"""
    # Create account and transactions
    acc_resp = client.post("/api/accounts/", json={"name": "Filter Test", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    client.post("/api/transactions/", json={
        "account_id": account_id,
        "date": datetime.now().isoformat(),
        "description": "Food",
        "amount": 50.0,
        "type": "expense",
        "category": "Food & Dining"
    })
    
    # Test filter by account
    response = client.get(f"/api/transactions/?account_id={account_id}")
    assert response.status_code == 200
    assert len(response.json()) >= 1

# Dashboard Tests
def test_dashboard_summary(client):
    """Test dashboard summary"""
    # Create account and transactions
    acc_resp = client.post("/api/accounts/", json={"name": "Dash Acc", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    client.post("/api/transactions/", json={
        "account_id": account_id,
        "date": datetime.now().isoformat(),
        "description": "Income",
        "amount": 2000.0,
        "type": "income",
        "category": "Salary"
    })
    
    client.post("/api/transactions/", json={
        "account_id": account_id,
        "date": datetime.now().isoformat(),
        "description": "Rent",
        "amount": 1000.0,
        "type": "expense",
        "category": "Bills & Utilities"
    })
    
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_balance" in data
    assert "monthly_income" in data
    assert "monthly_expenses" in data
    assert data["account_count"] >= 1

def test_dashboard_categories(client):
    """Test category breakdown endpoint"""
    # Create account and expense transactions
    acc_resp = client.post("/api/accounts/", json={"name": "Category Test", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    client.post("/api/transactions/", json={
        "account_id": account_id,
        "date": datetime.now().isoformat(),
        "description": "Groceries",
        "amount": 100.0,
        "type": "expense",
        "category": "Food & Dining"
    })
    
    response = client.get("/api/dashboard/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_dashboard_categories_filtered(client):
    """Test category breakdown with month/year filters"""
    # Create account and transactions in specific months
    acc_resp = client.post("/api/accounts/", json={"name": "Filter Chart Test", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    current_year = datetime.now().year
    
    # Transaction in Jan
    jan_date = datetime(current_year, 1, 15).isoformat()
    client.post("/api/transactions/", json={
        "account_id": account_id,
        "date": jan_date,
        "description": "Jan Expense",
        "amount": 100.0,
        "type": "expense",
        "category": "JanCat"
    })
    
    # Transaction in Feb
    feb_date = datetime(current_year, 2, 15).isoformat()
    client.post("/api/transactions/", json={
        "account_id": account_id,
        "date": feb_date,
        "description": "Feb Expense",
        "amount": 200.0,
        "type": "expense",
        "category": "FebCat"
    })
    
    # Filter for Jan
    resp_jan = client.get(f"/api/dashboard/categories?month=1&year={current_year}")
    assert resp_jan.status_code == 200
    data_jan = resp_jan.json()
    
    # Check if JanCat is present
    jan_entry = next((item for item in data_jan if item["category"] == "JanCat"), None)
    assert jan_entry is not None, "JanCat not found in January response"
    assert jan_entry["amount"] == 100.0
    
    # Filter for Feb
    resp_feb = client.get(f"/api/dashboard/categories?month=2&year={current_year}")
    assert resp_feb.status_code == 200
    data_feb = resp_feb.json()
    
    # Check if FebCat is present
    feb_entry = next((item for item in data_feb if item["category"] == "FebCat"), None)
    assert feb_entry is not None, "FebCat not found in February response"
    assert feb_entry["amount"] == 200.0

def test_category_timeseries(client):
    """Test category timeseries endpoint"""
    acc_resp = client.post("/api/accounts/", json={"name": "Timeseries Test", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    # Add some expenses
    client.post("/api/transactions/", json={
        "account_id": account_id,
        "date": datetime.now().isoformat(),
        "description": "Expense 1",
        "amount": 50.0,
        "type": "expense",
        "category": "Food"
    })
    
    response = client.get("/api/dashboard/category-timeseries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "date" in data[0]
        # Check if Food category is present (key might be dynamic)
        # We at least expect 'date' and some category keys
        assert len(data[0].keys()) >= 2
