"""Test script to verify Ollama integration with the finance tracker"""
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ollama_service import ollama_service

print("Testing Ollama Connection...\n")
print("=" * 60)

# Test 1: Classify a grocery transaction
print("\n1. Testing Transaction Classification (Grocery):")
print("-" * 60)
description = "Walmart - Grocery shopping"
amount = 150.50
result = ollama_service.classify_transaction(description, amount)
print(f"   Description: {description}")
print(f"   Amount: ${amount}")
print(f"   AI Classified Category: {result}")

# Test 2: Classify a salary transaction
print("\n2. Testing Transaction Classification (Salary):")
print("-" * 60)
description = "Monthly salary deposit"
amount = 5000.00
result = ollama_service.classify_transaction(description, amount)
print(f"   Description: {description}")
print(f"   Amount: ${amount}")
print(f"   AI Classified Category: {result}")

# Test 3: Classify a utility bill
print("\n3. Testing Transaction Classification (Utility):")
print("-" * 60)
description = "Electric company bill payment"
amount = 85.00
result = ollama_service.classify_transaction(description, amount)
print(f"   Description: {description}")
print(f"   Amount: ${amount}")
print(f"   AI Classified Category: {result}")

# Test 4: Classify entertainment
print("\n4. Testing Transaction Classification (Entertainment):")
print("-" * 60)
description = "Netflix subscription"
amount = 15.99
result = ollama_service.classify_transaction(description, amount)
print(f"   Description: {description}")
print(f"   Amount: ${amount}")
print(f"   AI Classified Category: {result}")

print("\n" + "=" * 60)
print("Ollama Integration Test Complete!")
print("=" * 60)
