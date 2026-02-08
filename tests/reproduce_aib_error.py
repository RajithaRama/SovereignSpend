import csv
import io
from datetime import datetime

def parse_aib_row(row):
    print(f"Processing row: {row}")
    
    # 1. Date: DD/MM/YY -> YYYY-MM-DD
    # BUG: The log says "02/01/2026", so it sends 4 digit year, but code expects 2 digit %y
    date_str = row.get('Posted Transactions Date', '').strip()
    formatted_date = date_str
    try:
        if date_str:
            # Replicating the bug: using %y for what might be 4 digit year
            dt = datetime.strptime(date_str, '%d/%m/%y')
            formatted_date = dt.strftime('%Y-%m-%d')
            print(f"Date parsed successfully: {formatted_date}")
    except ValueError as e:
        print(f"[WARN] Could not parse AIB date: {date_str} - {e}")
        
    # 2. Amount: Credit - Debit
    # BUG: float() fails on comma
    credit_str = row.get('Credit Amount', '').strip()
    debit_str = row.get('Debit Amount', '').strip()
    
    try:
        credit = float(credit_str) if credit_str else 0.0
        debit = float(debit_str) if debit_str else 0.0
        amount = credit - debit
        print(f"Amount parsed successfully: {amount}")
    except ValueError as e:
        print(f"Error reading CSV: {e}")

# Sample data mimicking the failed AIB CSV
csv_content = """Posted Transactions Date,Description,Debit Amount,Credit Amount
02/01/2026,Rent,1,500.00,
05/01/2026,Salary,,3,000.00
"""

reader = csv.DictReader(io.StringIO(csv_content), skipinitialspace=True)

print("--- Starting Reproduction ---")
for row in reader:
    parse_aib_row(row)
print("--- End Reproduction ---")
