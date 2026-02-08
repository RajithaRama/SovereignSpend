import sys
import os

# Ensure we can import from backend
sys.path.append(os.getcwd())

from backend.services.backup_service import perform_backup

def main():
    print("Starting manual backup process...")
    results = perform_backup(db_files=["finance_tracker.db", "finance_tracker_test.db"])
    
    success = True
    for result in results:
        if result['status'] == 'error':
            print(f"Failed to backup {result['file']}: {result['error']}")
            success = False
        elif result['status'] == 'skipped':
            print(f"Skipped {result['file']}: {result['reason']}")
    
    if success:
        print("Backup process completed successfully.")
    else:
        print("Backup process completed with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
