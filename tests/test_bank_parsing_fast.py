"""Test script for bank statement parsing with detailed logging using FAST model"""
import sys
import os
import time
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ollama_service import ollama_service

# FORCE REASONING MODEL
ollama_service.model = "deepseek-r1:latest" 

def test_parse_bank_statement():
    pdf_path = "test_data/sample_statement.pdf"  # Update with your test file
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 STARTING FAST TEST with model: {ollama_service.model}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📂 Target File: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File not found at {pdf_path}")
        return

    start_time = time.time()
    
    # Text Extraction
    text = ollama_service.extract_text_from_pdf(pdf_path)
    if not text:
        return

    text = text[:2000]
    
    # AI Parsing
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🤖 Sending to Ollama ({ollama_service.model})...")
    
    try:
        parsed_result = ollama_service.parse_bank_statement(pdf_path)
        
        elapsed = time.time() - start_time
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✅ COMPLETE! (took {elapsed:.2f}s)")
        
        transactions = parsed_result.get("transactions", [])
        print(f"   🎉 Found {len(transactions)} transactions")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_parse_bank_statement()
