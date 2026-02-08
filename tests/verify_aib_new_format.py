import os
import sys

# Add current directory to path to allow importing backend modules
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ollama_service import ollama_service

def test_aib_new_format():
    # Create a temporary CSV file with the problematic data
    csv_content = """Posted Account, Posted Transactions Date, Description1, Description2, Description3, Debit Amount, Credit Amount,Balance,Posted Currency,Transaction Type,Local Currency Amount,Local Currency
"933406 - 48256053","05/01/2026","D/D BOI Savings DS","IE26010513211203","","1,500.00",,"671.91",EUR,"Direct Debit"," 1,500.00",EUR
"933406 - 48256053","23/01/2026","2449000250","IE26012130059232","",,"6,515.52","6728.19",EUR,"Credit"," 6,515.52",EUR
"""
    test_file = "temp_test_aib_new.csv"
    with open(test_file, "w") as f:
        f.write(csv_content)
        
    try:
        print("Testing AIB parsing with new format logic...")
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
            # row 1: Debit="1,500.00" -> -1500.0
            expected_desc_1 = "D/D BOI Savings DS IE26010513211203"
            if t1['amount'] != -1500.0:
               print(f"FAILED: Transaction 1 amount mismatch. Expected -1500.0, got {t1['amount']}")
            if t1['description'] != expected_desc_1:
               print(f"FAILED: Transaction 1 description mismatch. Expected '{expected_desc_1}', got '{t1['description']}'")

            t2 = transactions[1]
            # row 2: Credit="6,515.52" -> 6515.52
            expected_desc_2 = "2449000250 IE26012130059232"
            if t2['amount'] != 6515.52:
               print(f"FAILED: Transaction 2 amount mismatch. Expected 6515.52, got {t2['amount']}")
            if t2['description'] != expected_desc_2:
               print(f"FAILED: Transaction 2 description mismatch. Expected '{expected_desc_2}', got '{t2['description']}'")

    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_aib_new_format()
