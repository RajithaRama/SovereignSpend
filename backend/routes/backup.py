from fastapi import APIRouter, HTTPException
from backend.services.backup_service import perform_backup

router = APIRouter(prefix="/api/backup", tags=["backup"])

@router.post("/")
def trigger_backup():
    """
    Trigger a manual backup of the databases.
    """
    try:
        results = perform_backup(["finance_tracker.db", "finance_tracker_test.db"])
        
        # Check for any failures
        failed = [res for res in results if res['status'] == 'error']
        if failed:
            raise HTTPException(status_code=500, detail=f"Backup failed for some files: {failed}")
            
        return {"message": "Backup completed successfully", "details": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
