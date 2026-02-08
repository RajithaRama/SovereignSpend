import pytest
import os
from unittest.mock import patch, MagicMock
from io import BytesIO

def test_upload_bank_statement_success(client):
    """Test successful bank statement upload and parsing"""
    # Create account
    acc_resp = client.post("/api/accounts/", json={"name": "Upload Test Acc", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    # Mock PDF and Ollama
    # Create a real BytesIO object for file content
    pdf_content = BytesIO(b"PDF Content")
    file = {"file": ("statement.pdf", pdf_content, "application/pdf")}
    
    with patch("backend.routes.upload.ollama_service.parse_bank_statement") as mock_parse:
        mock_parse.return_value = {
            "transactions": [
                {"date": "2024-01-01", "description": "Test Trans", "amount": -50.0}
            ]
        }
        with patch("backend.routes.upload.ollama_service.classify_transaction", return_value="Shopping"):
            
            # Setup mock file that returns bytes for hash calculation
            mock_file = MagicMock()
            mock_file.__enter__.return_value = mock_file
            mock_file.read.side_effect = [b"fake content", b""] # Return content then empty bytes for EOF
            
            with patch("builtins.open", return_value=mock_file):
                with patch("shutil.copyfileobj", MagicMock()):
                    with patch("os.remove", MagicMock()):
                        response = client.post(
                            "/api/upload/bank-statement",
                            files=file,
                            data={"account_id": account_id}
                        )
    
    assert response.status_code == 200
    assert response.json()["transactions_created"] == 1
    
    # Verify transaction created
    t_resp = client.get(f"/api/transactions/?account_id={account_id}")
    assert len(t_resp.json()) >= 1
    
def test_upload_bank_statement_parsing_failure(client):
    """Test that parsing failure prevents transaction creation"""
    # Create account
    acc_resp = client.post("/api/accounts/", json={"name": "Fail Test Acc", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    # Mock PDF and Ollama failure
    pdf_content = BytesIO(b"PDF Content")
    file = {"file": ("fail.pdf", pdf_content, "application/pdf")}
    
    with patch("backend.routes.upload.ollama_service.parse_bank_statement") as mock_parse:
        # Simulate error return
        mock_parse.return_value = {"error": "Parsing failed", "transactions": []}
        
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.read.side_effect = [b"fake content", b""] 

        with patch("builtins.open", return_value=mock_file):
            with patch("shutil.copyfileobj", MagicMock()):
                with patch("os.remove", MagicMock()):
                     response = client.post(
                        "/api/upload/bank-statement",
                        files=file,
                        data={"account_id": account_id}
                    )
    
    assert response.status_code == 500
    assert "Parsing failed" in response.json()["detail"]
    
    # Verify NO transactions created
    t_resp = client.get(f"/api/transactions/?account_id={account_id}")
    assert len(t_resp.json()) == 0

def test_upload_bank_statement_no_transactions(client):
    """Test that empty transaction list raises error"""
    # Create account
    acc_resp = client.post("/api/accounts/", json={"name": "Empty Test Acc", "balance": 1000})
    account_id = acc_resp.json()["id"]
    
    pdf_content = BytesIO(b"PDF Content")
    file = {"file": ("empty.pdf", pdf_content, "application/pdf")}
    
    with patch("backend.routes.upload.ollama_service.parse_bank_statement") as mock_parse:
        mock_parse.return_value = {"transactions": []}
        
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.read.side_effect = [b"fake content", b""] 
        
        with patch("builtins.open", return_value=mock_file):
            with patch("shutil.copyfileobj", MagicMock()):
                with patch("os.remove", MagicMock()):
                     response = client.post(
                        "/api/upload/bank-statement",
                        files=file,
                        data={"account_id": account_id}
                    )
    
    assert response.status_code == 500
    assert "No transactions found" in response.json()["detail"]
