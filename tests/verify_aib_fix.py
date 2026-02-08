import os
import sys

# Add current directory to path to allow importing backend modules
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ollama_service import ollama_service

def test_aib_parsing():
    # Create a temporary CSV file with the problematic data
    csv_content = """Posted Transactions Date,Description,Debit Amount,Credit Amount
02/01/2026,Rent,"1,500.00",
05/01/2026,Salary,,"3,000.00"
"""
    test_file = "temp_test_aib.csv"
    with open(test_file, "w") as f:
        f.write(csv_content)
        
    try:
        print("Testing AIB parsing with fixed logic...")
        result = ollama_service.parse_bank_statement(test_file, "AIB")
        
        if result.get("error"):
            print(f"FAILED: {result['error']}")
        else:
            transactions = result.get("transactions", [])
            print(f"SUCCESS: Parsed {len(transactions)} transactions")
            for t in transactions:
                print(f"  - {t['date']}: {t['description']} ({t['amount']})")
                
            # validations
            if len(transactions) != 2:
                print("FAILED: Expected 2 transactions")
                return
                
            t1 = transactions[0]
            if t1['amount'] != -1500.0: # Debit is negative in the logic? 
                # Logic: amount = credit - debit. 
                # Row 1: Debit="1,500.00", Credit="" -> 0 - 1500 = -1500. Matches.
                print(f"FAILED: Transaction 1 amount mismatch. Expected -1500.0, got {t1['amount']}")
                
            t2 = transactions[1]
            if t2['amount'] != 3000.0:
                # Row 2: Debit="", Credit="3,000.00" -> 3000 - 0 = 3000. Matches.
                print(f"FAILED: Transaction 2 amount mismatch. Expected 3000.0, got {t2['amount']}")

    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_aib_parsing()
