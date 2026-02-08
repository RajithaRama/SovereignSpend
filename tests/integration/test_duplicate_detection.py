
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from datetime import datetime, date

def test_manual_duplicate_detection(client):
    """Test the manual check-duplicates endpoint"""
    # Create account
    acc_resp = client.post("/api/accounts/", json={"name": "Dup Test Acc", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    # Create a transaction
    today = str(date.today())
    trans_data = {
        "account_id": account_id,
        "amount": 50.0,
        "type": "expense",
        "description": "Test Dup Item",
        "category": "Shopping",
        "date": datetime.now().isoformat()
    }
    client.post("/api/transactions/", json=trans_data)
    
    # Check for duplicates using the same data
    check_payload = trans_data.copy()
    check_payload["date"] = datetime.now().isoformat() # pass iso string
    # The client sends JSON, so it will be string.
    # We rely on pydantic to parse it in the endpoint.
    
    resp = client.post("/api/transactions/check-duplicates", json=check_payload)
    assert resp.status_code == 200
    duplicates = resp.json()
    assert len(duplicates) >= 1
    assert duplicates[0]["description"] == "Test Dup Item"

def test_upload_duplicate_detection(client):
    """Test that duplicates are skipped and reported during upload"""
    # Create account
    acc_resp = client.post("/api/accounts/", json={"name": "Upload Dup Test Acc", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    # Pre-seed a transaction
    client.post("/api/transactions/", json={
        "account_id": account_id,
        "amount": 100.0,
        "type": "expense",
        "description": "Unique Upload Item",
        "date": datetime(2025, 1, 1).isoformat()
    })
    
    # Mock CSV that contains the SAME transaction + a new one
    csv_content = """Posted Transactions Date,Description,Debit Amount,Credit Amount
01/01/25,Unique Upload Item,100.00,
02/01/25,New Unique Item,50.00,"""
    
    csv_bytes = csv_content.encode('utf-8')
    csv_file = BytesIO(csv_bytes)
    file = {"file": ("statement.csv", csv_file, "text/csv")}
    
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch("backend.routes.upload.STATEMENT_DIR", temp_dir):
            # We mock classify_transaction as that still uses AI for categorization
            with patch("backend.routes.upload.ollama_service.classify_transaction", return_value="Other"):
                # We mock file hash so it doesn't collide with other tests physically, 
                # but we let the file save happen.
                with patch("backend.routes.upload.calculate_file_hash", return_value="duphash_upload"):
                    resp = client.post(
                        "/api/upload/bank-statement",
                        files=file,
                        data={"account_id": account_id}
                    )
                            
    assert resp.status_code == 200
    data = resp.json()
    
    # We expect 1 created (the new one) and 1 duplicate found (the pres-seeded one)
    assert data["transactions_created"] == 1
    assert "duplicates_found" in data
    assert len(data["duplicates_found"]) == 1
    assert data["duplicates_found"][0]["description"] == "Unique Upload Item"
