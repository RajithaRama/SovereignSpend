from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import init_db
from backend.routes import accounts, transactions, upload, dashboard, backup
from backend.services.backup_service import perform_backup
import os

from backend.config_loader import load_rules

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    init_db()
    load_rules()
    yield
    # Shutdown actions
    print("Shutting down... Performing backup.")
    perform_backup(["finance_tracker.db", "finance_tracker_test.db"])

app = FastAPI(title="SovereignSpend API", lifespan=lifespan)

# CORS configuration to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(upload.router)
app.include_router(dashboard.router)
app.include_router(backup.router)

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "SovereignSpend API is running"}

# Serve static frontend files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
