"""Test script for bank statement parsing with detailed logging"""
import sys
import os
import time
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ollama_service import ollama_service

def test_parse_bank_statement():
    pdf_path = "test_data/sample_statement.pdf"  # Update with your test file
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 STARTING BANK STATEMENT TEST")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📂 Target File: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File not found at {pdf_path}")
        return

    start_time = time.time()
    
    # Step 1: Text Extraction
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📄 STEP 1: Extracting text from PDF...")
    try:
        text = ollama_service.extract_text_from_pdf(pdf_path)
        if text:
            print(f"   ✅ Extraction successful! ({len(text)} characters extracted)")
            print(f"   📝 Text Preview (first 500 chars):\n   " + "-"*40)
            print(f"   {text[:500].replace(chr(10), chr(10)+'   ')}")
            print("   " + "-"*40)
        else:
            print("   ❌ Extraction returned empty text")
            return
    except Exception as e:
        print(f"   ❌ Error extracting text: {e}")
        return

    # Step 2: AI Parsing
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🤖 STEP 2: Sending to Ollama for parsing...")
    print(f"   Using model: {ollama_service.model}")
    print(f"   Timeout setting: 600 seconds")
    print("   ⏳ Waiting for AI response (this may take a minute)...")
    
    try:
        parsed_result = ollama_service.parse_bank_statement(pdf_path)
        
        elapsed = time.time() - start_time
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✅ STEP 3: Processing Complete! (took {elapsed:.2f}s)")
        
        if "error" in parsed_result:
            print(f"   ❌ parsing failed: {parsed_result['error']}")
        else:
            transactions = parsed_result.get("transactions", [])
            print(f"   🎉 Successfully found {len(transactions)} transactions:")
            print("\n   " + "="*60)
            for i, tx in enumerate(transactions, 1):
                amount_str = f"${abs(tx.get('amount', 0)):.2f}"
                if tx.get('amount', 0) < 0:
                     amount_str = f"-{amount_str}"
                else:
                     amount_str = f"+{amount_str}"
                     
                print(f"   {i}. Date: {tx.get('date')} | Amount: {amount_str:<10} | Desc: {tx.get('description')}")
            print("   " + "="*60)
            
            # Dump full JSON for inspection
            print("\n   📦 Full JSON Result:")
            print(json.dumps(transactions, indent=2))
            
    except Exception as e:
        print(f"\n❌ Error during parsing: {e}")

if __name__ == "__main__":
    test_parse_bank_statement()
