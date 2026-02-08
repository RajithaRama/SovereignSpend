# Personal Finance Tracker 💰

A modern, AI-powered personal finance tracker with multi-account support, automated transaction classification, and beautiful data visualizations.

## Features

✨ **Multi-Account Management**
- Track multiple bank accounts
- Transfer funds between accounts
- Real-time balance updates

🤖 **AI-Powered Intelligence**
- Automatic transaction classification using Ollama (Qwen/Deepseek/Gemma)
- PDF invoice text extraction
- Bank statement parsing and transaction import

📊 **Comprehensive Dashboard**
- Financial overview with key metrics
- Timeseries charts for savings, earnings, and expenditure
- Category breakdown with interactive visualizations
- Per-account analytics

📱 **Modern UI**
- Glassmorphism design with dark mode
- Animated gradients and smooth transitions
- Responsive layout for all devices
- Drag-and-drop file uploads

## Tech Stack

**Backend:**
- Python 3.8+
- FastAPI
- SQLAlchemy (SQLite)
- Ollama AI Integration

**Frontend:**
- HTML5/CSS3/JavaScript
- Chart.js for visualizations
- Modern glassmorphism design

## Prerequisites

1. **Python 3.8 or higher**
2. **Ollama** - Install from [https://ollama.ai](https://ollama.ai)
3. **Ollama Models** - Pull at least one of these models:
   ```bash
   ollama pull qwen2.5
   ollama pull deepseek-r1
   ollama pull gemma2
   ```

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd path/to/finance-tracker
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - Windows (PowerShell):
     ```bash
     .\venv\Scripts\Activate.ps1
     ```
   - Windows (CMD):
     ```bash
     venv\Scripts\activate.bat
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Running the Application

1. **Start the server:**
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

2. **Open your browser:**
   Navigate to `http://localhost:8000`

## Usage Guide

### 1. Create Accounts
- Navigate to the "Accounts" tab
- Click "Add Account"
- Enter account name and initial balance

### 2. Add Transactions
- Go to "Transactions" tab
- Click "Add Transaction"
- Fill in details (category is optional - AI will classify it!)

### 3. Transfer Between Accounts
- In "Transactions" tab, click "Transfer"
- Select source and destination accounts
- Enter amount

### 4. Upload Documents

**Upload Invoice:**
- Go to "Upload" tab
- Drag and drop or click to upload PDF invoice
- AI will extract text automatically

**Upload Bank Statement:**
- Select the account
- Upload PDF bank statement
- AI will parse and create transactions automatically

### 5. View Dashboard
- The "Dashboard" tab shows:
  - Total balance across all accounts
  - Monthly income and expenses
  - Timeseries charts (savings, earnings, expenditure)
  - Category breakdown
  - Recent transactions
  - Per-account overview

## Configuration

Edit `.env` file to customize:

```env
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5
OLLAMA_FALLBACK_MODELS=deepseek-r1,gemma2
DATABASE_PATH=./finance_tracker.db
UPLOAD_DIR=./uploads
```

## API Documentation

Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints:

**Accounts:**
- `GET /api/accounts/` - List all accounts
- `POST /api/accounts/` - Create account
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Delete account

**Transactions:**
- `GET /api/transactions/` - List transactions (supports filtering)
- `POST /api/transactions/` - Create transaction (with AI classification)
- `POST /api/transactions/transfer` - Create transfer
- `DELETE /api/transactions/{id}` - Delete transaction

**Upload:**
- `POST /api/upload/invoice` - Upload and process invoice
- `POST /api/upload/bank-statement` - Upload and parse bank statement

**Dashboard:**
- `GET /api/dashboard/summary` - Overall summary
- `GET /api/dashboard/categories` - Category breakdown
- `GET /api/dashboard/timeseries` - Timeseries data
- `GET /api/dashboard/accounts-overview` - Per-account overview

## Project Structure

```
Finance tracker/
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── ollama_service.py       # AI integration
│   └── routes/
│       ├── accounts.py         # Account endpoints
│       ├── transactions.py     # Transaction endpoints
│       ├── upload.py           # File upload endpoints
│       └── dashboard.py        # Dashboard endpoints
├── frontend/
│   ├── index.html              # Main page
│   ├── styles.css              # Design system
│   ├── app.js                  # Core app logic
│   └── components/
│       ├── dashboard.js        # Dashboard component
│       ├── accounts.js         # Accounts component
│       ├── transactions.js     # Transactions component
│       └── upload.js           # Upload component
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Troubleshooting

**Ollama connection issues:**
- Ensure Ollama is running: `ollama serve`
- Check the configured URL in `.env`
- Verify models are installed: `ollama list`

**Database issues:**
- Delete `finance_tracker.db` to reset the database
- Restart the server

**File upload issues:**
- Ensure uploads directory exists
- Check file is a valid PDF
- Verify Ollama is responding

## Future Enhancements

- Budget planning and tracking
- Recurring transaction support
- Export to CSV/PDF
- Multi-currency support
- Email notifications
- Mobile app

## License

MIT License - Feel free to use and modify!

## Support

For issues or questions, please check:
1. Ollama is running and models are available
2. All dependencies are installed
3. Server logs for error messages

---

## Credits

Special thanks to the following AI models and teams for their support in building this project:
- **Gemini 3**
- **Claude Sonnet 4.5**
- **Google Antigravity**

---

Built with ❤️ using FastAPI, Ollama AI, and modern web technologies
