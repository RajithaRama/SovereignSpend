import requests
import json
import os
from dotenv import load_dotenv
from typing import Optional
import pypdf
import base64
from datetime import datetime

load_dotenv()

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3n:e4b")
FALLBACK_MODELS = os.getenv("OLLAMA_FALLBACK_MODELS", "deepseek-r1,gemma2").split(",")

class OllamaService:
    def __init__(self):
        self.api_url = OLLAMA_API_URL
        self.model = OLLAMA_MODEL
        self.fallback_models = FALLBACK_MODELS
    
    def _call_ollama(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """Call Ollama API with the given prompt"""
        try:
            model_to_use = model or self.model
            # Enable streaming to see thinking steps
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": model_to_use,
                    "prompt": prompt,
                    "stream": True
                },
                timeout=600,
                stream=True
            )
            
            if response.status_code == 200:
                full_response = ""
                print(f"\n[DEBUG] Streaming Response from {model_to_use}:")
                for line in response.iter_lines():
                    if line:
                        try:
                            json_response = json.loads(line)
                            chunk = json_response.get("response", "")
                            print(chunk, end="", flush=True)
                            full_response += chunk
                        except:
                            pass
                print("\n[END DEBUG]\n")
                return full_response.strip()
            else:
                print(f"Ollama API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error calling Ollama: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return None
    
    def classify_transaction(self, description: str, amount: float) -> Optional[str]:
        """Use Ollama to classify a transaction into a category"""
        prompt = f"""Classify the following transaction into one of these categories:
Categories: Food & Dining, Shopping, Transportation, Bills & Utilities, Entertainment, Healthcare, Travel, Income, Salary, Transfer, Other

Transaction: {description}
Amount: {amount}

Return ONLY the category name, nothing else."""

        # Try primary model first
        category = self._call_ollama(prompt, self.model)
        
        # If primary model fails, try fallback models
        if not category:
            for fallback_model in self.fallback_models:
                category = self._call_ollama(prompt, fallback_model.strip())
                if category:
                    break
        
        # Clean up the response
        if category:
            category = category.strip().strip('"\'')
            # Ensure it's a valid category
            valid_categories = [
                "Food & Dining", "Shopping", "Transportation", "Bills & Utilities",
                "Entertainment", "Healthcare", "Travel", "Income", "Salary", "Transfer", "Other"
            ]
            if category in valid_categories:
                return category
        
        return "Other"  # Default fallback
    
    def extract_invoice_data(self, pdf_path: str) -> dict:
        """Extract structured data from invoice PDF using Ollama"""
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {"error": "Could not extract text from PDF"}
        
        prompt = f"""Extract the following information from this invoice text:
- Total amount (just the number)
- Date (in YYYY-MM-DD format if possible)
- Vendor/Company name
- Brief description

Invoice text:
{text[:2000]}  

Return your response in JSON format like this:
{{"amount": 123.45, "date": "2024-01-15", "vendor": "Company Name", "description": "Brief description"}}

Return ONLY valid JSON, nothing else."""

        result = self._call_ollama(prompt)
        
        if result:
            try:
                # Try to parse JSON from the result
                # Sometimes the model adds extra text, so we try to extract JSON
                start_idx = result.find('{')
                end_idx = result.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = result[start_idx:end_idx]
                    data = json.loads(json_str)
                    data['raw_text'] = text
                    return data
            except json.JSONDecodeError:
                pass
        
        # Fallback: return raw text
        return {
            "raw_text": text,
            "error": "Could not parse structured data"
        }
    
    def parse_bank_statement(self, filepath: str, bank_name: str = "AIB") -> dict:
        """Parse bank statement (PDF or CSV) and extract transactions"""
        all_transactions = []
        foreign_transactions = []
        full_text = ""
        
        try:
            file_ext = os.path.splitext(filepath)[1].lower()
            
            if file_ext == '.csv':
                # Handle CSV parsing deterministically
                import csv
                try:
                    # Parse CSV directly without AI
                    with open(filepath, 'r', encoding='utf-8') as f:
                        # Read file content for raw_text return
                        full_text = f.read()
                        # Seek back to start for parsing
                        f.seek(0)
                        
                        # Use skipinitialspace=True to handle spaces after commas (common in described format)
                        reader = csv.DictReader(f, skipinitialspace=True)
                        
                        for row in reader:
                            # Parse based on bank name
                            if bank_name == "Revolut":
                                # Revolut Format: Type, Product, Started Date, Completed Date, Description, Amount, Fee, Currency, State, Balance
                                
                                # 1. Date: parse 'Completed Date' (e.g., "2025-01-01 09:06:57")
                                date_str = row.get('Completed Date', '').strip()
                                
                                # Fallback to 'Started Date' if Completed Date is empty (e.g. Pending/Reverted)
                                if not date_str:
                                    date_str = row.get('Started Date', '').strip()
                                    
                                formatted_date = date_str
                                try:
                                    if date_str:
                                        # Handle ISO format "YYYY-MM-DD HH:MM:SS"
                                        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                                        formatted_date = dt.strftime('%Y-%m-%d')
                                except ValueError:
                                    # Fallback or other formats
                                    try:
                                        dt = datetime.fromisoformat(date_str)
                                        formatted_date = dt.strftime('%Y-%m-%d')
                                    except:
                                        # print(f"[WARN] Could not parse Revolut date: {date_str}")
                                        pass

                                # 2. Description
                                desc = row.get('Description', '').strip()

                                # 3. Amount
                                amount_str = row.get('Amount', '').strip()
                                amount = float(amount_str) if amount_str else 0.0
                                
                                # 4. Currency validation
                                currency = row.get('Currency', '').strip()
                                
                                if desc:
                                    transaction_data = {
                                        "date": formatted_date,
                                        "description": desc,
                                        "amount": amount
                                    }
                                    
                                    # Check if currency is EUR
                                    if currency == 'EUR':
                                        all_transactions.append(transaction_data)
                                    else:
                                        # Add currency info for foreign transactions
                                        transaction_data['currency'] = currency
                                        foreign_transactions.append(transaction_data)

                            else: 
                                # Default to AIB (Existing logic)
                                # Map columns based on known AIB format:
                                # "Posted Transactions Date", "Description", "Debit Amount", "Credit Amount"
                                
                                # 1. Date: DD/MM/YY -> YYYY-MM-DD
                                date_str = row.get('Posted Transactions Date', '').strip()
                                formatted_date = date_str
                                try:
                                    if date_str:
                                        # Try 4-digit year first, then 2-digit
                                        try:
                                            dt = datetime.strptime(date_str, '%d/%m/%Y')
                                        except ValueError:
                                            dt = datetime.strptime(date_str, '%d/%m/%y')
                                        formatted_date = dt.strftime('%Y-%m-%d')
                                except ValueError:
                                    print(f"[WARN] Could not parse AIB date: {date_str}")
                                    pass
                                    
                                # 2. Description
                                if 'Description' in row:
                                    desc = row.get('Description', '').strip()
                                else:
                                    # Handle case where description is split across multiple columns
                                    d1 = row.get('Description1', '').strip()
                                    d2 = row.get('Description2', '').strip()
                                    d3 = row.get('Description3', '').strip()
                                    desc = f"{d1} {d2} {d3}".strip()
                                
                                # 3. Currency validation and amount extraction
                                posted_currency = row.get('Posted Currency', '').strip()
                                local_currency = row.get('Local Currency', '').strip()
                                
                                # Determine which amount to use
                                if posted_currency == 'EUR':
                                    # Use Posted amounts (Credit/Debit)
                                    credit_str = row.get('Credit Amount', '').strip().replace(',', '')
                                    debit_str = row.get('Debit Amount', '').strip().replace(',', '')
                                    
                                    credit = float(credit_str) if credit_str else 0.0
                                    debit = float(debit_str) if debit_str else 0.0
                                    
                                    amount = credit - debit
                                elif local_currency == 'EUR':
                                    # Use Local Currency Amount
                                    local_amount_str = row.get('Local Currency Amount', '').strip().replace(',', '')
                                    
                                    # Determine if it's credit or debit based on the Posted amounts
                                    credit_str = row.get('Credit Amount', '').strip().replace(',', '')
                                    debit_str = row.get('Debit Amount', '').strip().replace(',', '')
                                    
                                    # Parse local amount
                                    local_amount = float(local_amount_str) if local_amount_str else 0.0
                                    
                                    # Determine sign based on which field (Credit/Debit) was populated
                                    if credit_str:
                                        amount = abs(local_amount)  # Credit is positive
                                    elif debit_str:
                                        amount = -abs(local_amount)  # Debit is negative
                                    else:
                                        amount = local_amount
                                else:
                                    # Neither Posted nor Local currency is EUR - add to foreign transactions
                                    if desc:
                                        credit_str = row.get('Credit Amount', '').strip().replace(',', '')
                                        debit_str = row.get('Debit Amount', '').strip().replace(',', '')
                                        
                                        credit = float(credit_str) if credit_str else 0.0
                                        debit = float(debit_str) if debit_str else 0.0
                                        
                                        amount = credit - debit
                                        
                                        foreign_transactions.append({
                                            "date": formatted_date,
                                            "description": desc,
                                            "amount": amount,
                                            "currency": posted_currency
                                        })
                                    continue  # Skip adding to all_transactions
                                
                                if desc: # Only add if description exists
                                    all_transactions.append({
                                        "date": formatted_date,
                                        "description": desc,
                                        "amount": amount
                                    })
                            
                    print(f"[DEBUG] Parsed {len(all_transactions)} transactions from CSV using logic for {bank_name}")
                    if foreign_transactions:
                        print(f"[DEBUG] Found {len(foreign_transactions)} foreign currency transactions")
                    
                except Exception as e:
                     print(f"Error reading CSV: {str(e)}")
                     return {"transactions": [], "raw_text": full_text, "error": f"Error reading CSV: {str(e)}"}

            else:
                # Handle PDF parsing (existing logic)
                with open(filepath, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    num_pages = len(pdf_reader.pages)
                    print(f"[DEBUG] Processing PDF with {num_pages} pages...")
                    
                    for i, page in enumerate(pdf_reader.pages):
                        print(f"[DEBUG] Parsing page {i+1}/{num_pages}...")
                        page_text = page.extract_text()
                        if not page_text.strip():
                            continue
                            
                        full_text += page_text + "\n"
                        
                        prompt = f"""Extract all transactions from this bank statement page. For each transaction, identify:
- Date (YYYY-MM-DD format)
- Description
- Amount (positive for credits, negative for debits)

Page content:
{page_text}

Return your response as a JSON array of transactions like this:
[
  {{"date": "2024-01-15", "description": "Grocery Store", "amount": -45.50}},
  {{"date": "2024-01-16", "description": "Salary Deposit", "amount": 3000.00}}
]

Return ONLY valid JSON array, nothing else. If no transactions are found on this page, return an empty array []."""

                        # Call Ollama
                        result = self._call_ollama(prompt)
                        
                        if result:
                            try:
                                # Try to find JSON array in response
                                start_idx = result.find('[')
                                end_idx = result.rfind(']') + 1
                                if start_idx >= 0 and end_idx > start_idx:
                                    json_str = result[start_idx:end_idx]
                                    page_transactions = json.loads(json_str)
                                    if isinstance(page_transactions, list):
                                        print(f"[DEBUG] Found {len(page_transactions)} transactions on page {i+1}")
                                        all_transactions.extend(page_transactions)
                            except json.JSONDecodeError:
                                print(f"[WARN] Failed to parse JSON for page {i+1}")
                                pass
                                
            return {
                "transactions": all_transactions, 
                "foreign_transactions": foreign_transactions,
                "raw_text": full_text
            }
            
        except Exception as e:
            print(f"Error parsing bank statement: {str(e)}")
            return {"transactions": [], "raw_text": full_text, "error": f"Could not parse transactions: {str(e)}"}

# Singleton instance
ollama_service = OllamaService()
