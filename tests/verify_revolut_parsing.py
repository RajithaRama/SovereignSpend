import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.ollama_service import ollama_service
import json

def verify_revolut_parsing():
    # Example CSV path - update with your own Revolut statement file
    file_path = "test_data/sample_revolut_statement.csv"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Testing parsing for: {file_path}")
    
    # Test with bank_name="Revolut"
    result = ollama_service.parse_bank_statement(file_path, bank_name="Revolut")
    
    if result.get("error"):
        print(f"Error: {result['error']}")
    else:
        transactions = result.get("transactions", [])
        print(f"Successfully parsed {len(transactions)} transactions.")
        if len(transactions) > 0:
            print("First 3 transactions:")
            for t in transactions[:3]:
                print(json.dumps(t, indent=2))
                
            # Verification checks
            # Check 1: Date format should be YYYY-MM-DD
            # Check 2: Amount should be float
            # Check 3: Description should not be empty
            
            valid_dates = all(len(t['date'].split('-')) == 3 for t in transactions)
            print(f"Dates valid: {valid_dates}")
            
            valid_amounts = all(isinstance(t['amount'], float) for t in transactions)
            print(f"Amounts valid: {valid_amounts}")
            
    print("-" * 30)
    
    # Test with default (AIB) - should fail or produce garbage/empty if it doesn't match columns
    print("Testing with default bank (AIB) - Expecting mainly empty or warned output due to column mismatch")
    result_aib = ollama_service.parse_bank_statement(file_path, bank_name="AIB")
    print(f"Transactions found with AIB logic: {len(result_aib.get('transactions', []))}")

if __name__ == "__main__":
    verify_revolut_parsing()
