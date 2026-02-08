"""
Test currency validation for bank statement parsing
"""
import os
import sys
import pytest
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ollama_service import ollama_service


def test_revolut_foreign_currency_separation():
    """Test that Revolut non-EUR transactions are separated into foreign_transactions"""
    # Create a temporary CSV file with mixed currencies
    csv_content = """Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Card Payment,Current,2025-01-01 09:00:00,2025-01-01 10:00:00,Test EUR Transaction,-10.00,0.00,EUR,COMPLETED,90.00
Card Payment,Current,2025-01-02 09:00:00,2025-01-02 10:00:00,Test USD Transaction,-15.00,0.00,USD,COMPLETED,75.00
Card Payment,Current,2025-01-03 09:00:00,2025-01-03 10:00:00,Test GBP Transaction,-20.00,0.00,GBP,COMPLETED,55.00
"""
    
    test_file = "temp_test_revolut_currency.csv"
    with open(test_file, "w") as f:
        f.write(csv_content)
    
    try:
        result = ollama_service.parse_bank_statement(test_file, "Revolut")
        
        # Check that EUR transaction is in main list
        assert len(result["transactions"]) == 1
        assert result["transactions"][0]["description"] == "Test EUR Transaction"
        assert result["transactions"][0]["amount"] == -10.00
        
        # Check that foreign transactions are separated
        assert len(result["foreign_transactions"]) == 2
        
        # Check USD transaction
        usd_trans = next(t for t in result["foreign_transactions"] if t["currency"] == "USD")
        assert usd_trans["description"] == "Test USD Transaction"
        assert usd_trans["amount"] == -15.00
        
        # Check GBP transaction
        gbp_trans = next(t for t in result["foreign_transactions"] if t["currency"] == "GBP")
        assert gbp_trans["description"] == "Test GBP Transaction"
        assert gbp_trans["amount"] == -20.00
        
        print("✓ Revolut foreign currency separation test passed")
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_aib_local_currency_fallback():
    """Test that AIB uses Local Currency Amount when Posted Currency is not EUR"""
    # Create a temporary CSV file with non-EUR Posted Currency but EUR Local Currency
    csv_content = """Posted Account, Posted Transactions Date, Description1, Description2, Description3, Debit Amount, Credit Amount,Balance,Posted Currency,Transaction Type,Local Currency Amount,Local Currency
"933406 - 48256053","05/01/2026","Test Transaction","","","100.00",,"500.00",USD,"Debit"," 90.00",EUR
"933406 - 48256053","06/01/2026","Test EUR Transaction","","","50.00",,"450.00",EUR,"Debit"," 50.00",EUR
"""
    
    test_file = "temp_test_aib_currency.csv"
    with open(test_file, "w") as f:
        f.write(csv_content)
    
    try:
        result = ollama_service.parse_bank_statement(test_file, "AIB")
        
        # Both transactions should be in main list (one uses Posted, one uses Local)
        assert len(result["transactions"]) == 2
        
        # First transaction should use Local Currency Amount (90.00)
        trans1 = result["transactions"][0]
        assert trans1["description"] == "Test Transaction"
        assert trans1["amount"] == -90.00  # Debit is negative
        
        # Second transaction should use Posted Amount (50.00)
        trans2 = result["transactions"][1]
        assert trans2["description"] == "Test EUR Transaction"
        assert trans2["amount"] == -50.00
        
        # No foreign transactions
        assert len(result["foreign_transactions"]) == 0
        
        print("✓ AIB local currency fallback test passed")
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_aib_neither_currency_is_eur():
    """Test that AIB transactions with neither Posted nor Local currency as EUR are separated"""
    csv_content = """Posted Account, Posted Transactions Date, Description1, Description2, Description3, Debit Amount, Credit Amount,Balance,Posted Currency,Transaction Type,Local Currency Amount,Local Currency
"933406 - 48256053","05/01/2026","Foreign Transaction","","","100.00",,"500.00",USD,"Debit"," 110.00",GBP
"""
    
    test_file = "temp_test_aib_foreign.csv"
    with open(test_file, "w") as f:
        f.write(csv_content)
    
    try:
        result = ollama_service.parse_bank_statement(test_file, "AIB")
        
        # No EUR transactions
        assert len(result["transactions"]) == 0
        
        # Should have one foreign transaction
        assert len(result["foreign_transactions"]) == 1
        assert result["foreign_transactions"][0]["description"] == "Foreign Transaction"
        assert result["foreign_transactions"][0]["currency"] == "USD"
        
        print("✓ AIB foreign currency separation test passed")
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


if __name__ == "__main__":
    print("Running currency validation tests...\n")
    test_revolut_foreign_currency_separation()
    test_aib_local_currency_fallback()
    test_aib_neither_currency_is_eur()
    print("\n✓ All currency validation tests passed!")
