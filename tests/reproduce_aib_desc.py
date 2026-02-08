import csv
import io
from datetime import datetime

def parse_aib_row(row):
    print(f"Processing row keys: {list(row.keys())}")
    
    # Existing Logic from backend/ollama_service.py
    desc = row.get('Description', '').strip()
    print(f"Parsed Description: '{desc}'")
    
    if not desc:
        print("SKIP: Description is empty (Current Logic Failure)")
        
        # Proposed Fix: Check for Description1, Description2, Description3
        d1 = row.get('Description1', '').strip()
        d2 = row.get('Description2', '').strip()
        d3 = row.get('Description3', '').strip()
        
        combined_desc = f"{d1} {d2} {d3}".strip()
        print(f"Proposed Fix Description: '{combined_desc}'")

# Sample data from the user's file
csv_content = """Posted Account, Posted Transactions Date, Description1, Description2, Description3, Debit Amount, Credit Amount,Balance,Posted Currency,Transaction Type,Local Currency Amount,Local Currency
"933406 - 48256053","05/01/2026","D/D BOI Savings DS","IE26010513211203","","1,500.00",,"671.91",EUR,"Direct Debit"," 1,500.00",EUR
"""

reader = csv.DictReader(io.StringIO(csv_content), skipinitialspace=True)

print("--- Starting Reproduction ---")
for row in reader:
    parse_aib_row(row)
print("--- End Reproduction ---")
