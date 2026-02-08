import sqlite3
import os
import datetime
import glob
import shutil

# Configuration
BACKUP_DIR = "backups"
DB_FILES = ["finance_tracker.db", "finance_tracker_test.db"]
MAX_BACKUPS = 10

def perform_backup(db_files=None, backup_dir=None, max_backups=None):
    """
    Performs a backup of the specified database files.
    """
    if db_files is None:
        db_files = DB_FILES
    if backup_dir is None:
        backup_dir = BACKUP_DIR
    if max_backups is None:
        max_backups = MAX_BACKUPS

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"Created backup directory: {backup_dir}")

    results = []
    
    for db_file in db_files:
        if not os.path.exists(db_file):
            print(f"Skipping {db_file}: File not found.")
            results.append({"file": db_file, "status": "skipped", "reason": "File not found"})
            continue

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{os.path.basename(db_file)}_{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            # Use SQLite backup API for safe backup during runtime
            source_conn = sqlite3.connect(db_file)
            dest_conn = sqlite3.connect(backup_path)
            
            with dest_conn:
                source_conn.backup(dest_conn)
            
            dest_conn.close()
            source_conn.close()
            
            print(f"Successfully backed up {db_file} to {backup_path}")
            cleanup_old_backups(db_file, backup_dir, max_backups)
            results.append({"file": db_file, "status": "success", "backup_path": backup_path})
            
        except sqlite3.Error as e:
            error_msg = f"Error backing up {db_file}: {e}"
            print(error_msg)
            results.append({"file": db_file, "status": "error", "error": str(e)})
        except Exception as e:
            error_msg = f"Unexpected error backing up {db_file}: {e}"
            print(error_msg)
            results.append({"file": db_file, "status": "error", "error": str(e)})
            
    return results

def cleanup_old_backups(db_file, backup_dir, max_backups):
    base_name = os.path.basename(db_file)
    pattern = os.path.join(backup_dir, f"{base_name}_*.bak")
    backups = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    
    if len(backups) > max_backups:
        for old_backup in backups[max_backups:]:
            try:
                os.remove(old_backup)
                print(f"Removed old backup: {old_backup}")
            except OSError as e:
                print(f"Error removing {old_backup}: {e}")
