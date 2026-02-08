import requests
import os

BASE_URL = "http://localhost:8000/api"
PDF_PATH = "test_data/sample_invoice.pdf"  # Update with your test file

def test_duplicate_upload():
    print("Testing duplicate upload prevention...")
    
    # 1. Ensure account exists (Account 1)
    # We assume Account 1 exists or we fetch one
    accounts = requests.get(f"{BASE_URL}/accounts/").json()
    if not accounts:
        print("Creating test account...")
        requests.post(f"{BASE_URL}/accounts/", json={"name": "Test Acct", "balance": 1000})
        accounts = requests.get(f"{BASE_URL}/accounts/").json()
    
    account_id = accounts[0]['id']
    print(f"Using Account ID: {account_id}")

    # 2. Upload file first time
    print("\nUploading file (Attempt 1)...")
    with open(PDF_PATH, 'rb') as f:
        files = {'file': f}
        data = {'account_id': account_id}
        # Note: This might trigger Ollama which is slow. We might want to mock or just expect it to proceed past duplicate check.
        # But wait, duplicate check is BEFORE Ollama.
        # However, the FIRST upload WILL trigger Ollama and might take time.
        # We can interrupt it or just wait.
        # Since I just want to test duplicate check, I can let the first one run (maybe timeout) but if it saves to DB, the hash is saved.
        
        # Actually, if Ollama fails (timeout), the transaction might rollback?
        # Let's check upload.py structure.
        # db.add(db_statement); db.commit() happens BEFORE Ollama.
        # So even if Ollama fails/timeouts, the record exists with "processing" status and the HASH.
        # Perfect.
        
        try:
             response = requests.post(f"{BASE_URL}/upload/bank-statement", files=files, data=data, timeout=5)
             print(f"Response: {response.status_code}")
        except requests.exceptions.Timeout:
             print("Request timed out (expected due to Ollama), but DB record should be created.")
        except Exception as e:
             print(f"Error: {e}")

    # 3. Upload file second time
    print("\nUploading file (Attempt 2) - SHOULD FAIL...")
    with open(PDF_PATH, 'rb') as f:
        files = {'file': f}
        data = {'account_id': account_id}
        response = requests.post(f"{BASE_URL}/upload/bank-statement", files=files, data=data)
        
        if response.status_code == 409:
            print("✅ SUCCESS: Duplicate detected (409 Conflict)")
            print(f"Message: {response.json()['detail']}")
        else:
            print(f"❌ FAILURE: Expected 409, got {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    test_duplicate_upload()
