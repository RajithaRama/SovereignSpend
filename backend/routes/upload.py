from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Invoice, BankStatement, Transaction, Account, TransactionRule
from backend.ollama_service import ollama_service
from backend.schemas import InvoiceUploadResponse
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
INVOICE_DIR = os.path.join(UPLOAD_DIR, "invoices")
STATEMENT_DIR = os.path.join(UPLOAD_DIR, "statements")

# Create upload directories if they don't exist
os.makedirs(INVOICE_DIR, exist_ok=True)
os.makedirs(STATEMENT_DIR, exist_ok=True)

import hashlib

def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

@router.post("/invoice", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process PDF invoice with AI text extraction"""
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save file temporarily
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(INVOICE_DIR, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Calculate hash and check for duplicates
    file_hash = calculate_file_hash(filepath)
    existing_invoice = db.query(Invoice).filter(Invoice.file_hash == file_hash).first()
    
    if existing_invoice:
        # Delete duplicate file
        os.remove(filepath)
        raise HTTPException(status_code=409, detail=f"Duplicate invoice detected. Already uploaded as {existing_invoice.filename}")
    
    # Extract data using Ollama
    invoice_data = ollama_service.extract_invoice_data(filepath)
    
    # Create invoice record
    db_invoice = Invoice(
        filename=filename,
        filepath=filepath,
        extracted_text=invoice_data.get("raw_text", ""),
        file_hash=file_hash
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    return InvoiceUploadResponse(
        id=db_invoice.id,
        filename=db_invoice.filename,
        extracted_text=invoice_data.get("raw_text", "")[:500],  # Return first 500 chars
        uploaded_at=db_invoice.uploaded_at
    )

@router.post("/bank-statement")
async def upload_bank_statement(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    bank_name: str = Form("AIB"),
    force: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Upload and parse PDF bank statement with AI"""
    # Validate file type
    if not (file.filename.lower().endswith('.pdf') or file.filename.lower().endswith('.csv')):
        raise HTTPException(status_code=400, detail="Only PDF and CSV files are supported")
    
    # Verify account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(STATEMENT_DIR, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Calculate hash and check for duplicates
    file_hash = calculate_file_hash(filepath)
    existing_statement = db.query(BankStatement).filter(BankStatement.file_hash == file_hash).first()
    
    if existing_statement and not force:
        # Delete duplicate file
        os.remove(filepath)
        raise HTTPException(status_code=409, detail=f"Duplicate bank statement detected. Already uploaded as {existing_statement.filename}")
    
    # Create bank statement record
    db_statement = BankStatement(
        account_id=account_id,
        filename=filename,
        filepath=filepath,
        parsed_status="processing",
        file_hash=file_hash
    )
    db.add(db_statement)
    db.commit()
    
    # Parse statement using Ollama
    try:
        parsed_data = ollama_service.parse_bank_statement(filepath, bank_name)
        
        # Check for parsing errors
        if parsed_data.get("error"):
            raise Exception(parsed_data["error"])
            
        transactions = parsed_data.get("transactions", [])
        foreign_transactions = parsed_data.get("foreign_transactions", [])
        
        if not transactions and not foreign_transactions:
            raise Exception("No transactions found in statement or parsing failed")
        
        # Create transactions from parsed data
        created_count = 0
        duplicates_found = []
        
        # Flush the statement to get an ID but don't commit yet
        # This keeps the transaction open
        db.flush()
        
        for trans_data in transactions:
            try:
                amount = float(trans_data.get("amount", 0))
                # Skip zero amount transactions
                if amount == 0:
                    continue
                    
                # Determine type based on amount sign if not provided
                # Usually negative is expense, positive is income in bank exports
                # But we store strict positive amounts with type
                
                is_expense = amount < 0
                abs_amount = abs(amount)
                trans_type = "expense" if is_expense else "income"
                
                # Parse date
                date_str = trans_data.get("date")
                try:
                    trans_date = datetime.fromisoformat(date_str)
                except:
                    trans_date = datetime.now()
                
                description = trans_data.get("description", "Bank transaction")
                
                # Check for duplicates before creating
                # Strict check: Same Account, Same Date (Day), Same Amount, Same Description (case-insensitive)
                start_of_day = datetime.combine(trans_date.date(), datetime.min.time())
                end_of_day = datetime.combine(trans_date.date(), datetime.max.time())
                
                existing = db.query(Transaction).filter(
                    Transaction.account_id == account_id,
                    Transaction.amount == abs_amount,
                    Transaction.type == trans_type,
                    Transaction.description.ilike(description),
                    Transaction.date >= start_of_day,
                    Transaction.date <= end_of_day
                ).first()
                
                if existing:
                    duplicates_found.append({
                        "date": date_str,
                        "description": description,
                        "amount": amount, # original signed amount
                        "type": trans_type,
                        "category": existing.category # Use existing category hint
                    })
                    continue

                # Classify transaction
                category = ollama_service.classify_transaction(description, abs_amount)
                
                # Create transaction
                transaction = Transaction(
                    account_id=account_id,
                    amount=abs_amount,
                    type=trans_type,
                    category=category,
                    description=description,
                    date=trans_date
                )
                db.add(transaction)
                
                # Update account balance
                if trans_type == "income":
                    account.balance += abs_amount
                else:
                    account.balance -= abs_amount
                
                created_count += 1
                
                created_count += 1
                
                # Apply Transaction Rules using RulesEngine
                from backend.services.rules_engine import RulesEngine
                engine = RulesEngine(db)
                engine.apply_rules(transaction)
            except Exception as e:
                print(f"Error creating transaction: {e}")
                continue
        
        if created_count == 0 and len(duplicates_found) == 0:
             raise Exception("Failed to create any valid transactions from parsed data")

        db_statement.parsed_status = "completed"
        db.commit()
        
        return {
            "message": "Bank statement uploaded and parsed successfully",
            "statement_id": db_statement.id,
            "transactions_created": created_count,
            "raw_transactions": len(transactions),
            "duplicates_found": duplicates_found,
            "foreign_transactions": foreign_transactions
        }
    except Exception as e:
        # Rollback any pending changes (transactions, account updates)
        db.rollback()
        
        # Start a new transaction to record the failure status
        # We need to re-fetch or re-attach the statement if it was detached
        # But simpler to just query it again or handle it in a fresh session if needed.
        # However, since we rolled back, the statement insertion inside THIS session is also rolled back?
        # WAIT. We wanted to keep the statement but mark it as failed? 
        # Actually, the user requirement says "Only add the bak transcript data when the parsing successfull."
        # It implies we might not even want the statement record if it fails? 
        # But usually we want to see that an upload failed.
        
        # Re-add the statement with failed status
        # Since rollback removed the previous add()
        
        try:
             # Check if we can still use the statement object or need to recreate
             # Ideally we want to keep the record of the attempt
             
             # Re-create the statement record for the log
             failed_statement = BankStatement(
                account_id=account_id,
                filename=filename,
                filepath=filepath,
                parsed_status="failed",
                file_hash=file_hash
            )
             db.add(failed_statement)
             db.commit()
        except Exception as write_err:
            print(f"Error saving failed status: {write_err}")
            
        raise HTTPException(status_code=500, detail=f"Error parsing statement: {str(e)}")
