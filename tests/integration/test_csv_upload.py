import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

def test_upload_csv_bank_statement(client):
    """Test successful CSV bank statement upload and parsing"""
    # Create account
    acc_resp = client.post("/api/accounts/", json={"name": "CSV Test Acc", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    # Mock CSV content based on user example
    csv_content_str = """Posted Account, Posted Transactions Date, Description, Debit Amount, Credit Amount,Balance,Transaction Type
933406-48256053,03/02/26,"*MOBI FEB RENT",1670.00,,4889.20,Debit
933406-48256053,23/01/26,"2449000250",,6515.52,,Credit"""
    
    csv_bytes = csv_content_str.encode('utf-8')
    csv_file = BytesIO(csv_bytes)
    
    # Mock CSV file upload
    file = {"file": ("statement.csv", csv_file, "text/csv")}
    
    # Create a real temp file for the test to avoid complex mocking of open()
    # The system under test (upload.py -> ollama_service.py) reads this file from disk.
    
    import os
    import tempfile
    import shutil
    
    # We need to control where the upload endpoint "saves" the file so that
    # ollama_service reads the file we created.
    # However, upload.py saves it to STATEMENT_DIR.
    # We can just let upload.py save it (it's running in the test process), 
    # but we need to ensure we don't pollute the real uploads folder.
    # Or, we can mock `shutil.copyfileobj` to WRITE to our temp file?
    # No, upload.py determines the destination path.
    
    # Strat: Let's Mock `shutil.copyfileobj` to be a no-op, 
    # BUT Mock `calculate_file_hash` and `ollama_service.parse_bank_statement`?
    # NO, we want to test `parse_bank_statement`.
    
    # Strat: 
    # 1. Create a temp file `temp_csv`.
    # 2. Mock `upload.STATEMENT_DIR` to be a temp dir?
    # 3. Let upload.py save the file there.
    # 4. Cleanup after test.
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Patch the STATEMENT_DIR in upload.py
        with patch("backend.routes.upload.STATEMENT_DIR", temp_dir):
            # We also need to patch calculate_file_hash because it reads the file.
            # But since we are letting the file be saved really, calculate_file_hash should work!
            
            # The only thing is `file` in upload_bank_statement came from client.post
            # FastAPI TestClient sends data. upload.py saves it.
            
            # So we don't need to mock open() or copyfileobj! 
            # We just need to ensure the destination is safe (temp dir).
            
            # We DO need to mock classify_transaction as it uses AI.
            with patch("backend.routes.upload.ollama_service.classify_transaction", return_value="Rent"):
                 response = client.post(
                    "/api/upload/bank-statement",
                    files=file,
                    data={"account_id": account_id}
                )

    assert response.status_code == 200
    assert response.json()["transactions_created"] == 2
    
    # Verify transactions
    t_resp = client.get(f"/api/transactions/?account_id={account_id}")
    transactions = t_resp.json()
    assert len(transactions) >= 2
    
    # Verify values
    rent_trans = next(t for t in transactions if "RENT" in t["description"])
    assert rent_trans["amount"] == 1670.00
    assert rent_trans["type"] == "expense"
    
    credit_trans = next(t for t in transactions if "2449000250" in t["description"])
    assert credit_trans["amount"] == 6515.52
    assert credit_trans["type"] == "income"
