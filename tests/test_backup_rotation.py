import os
import sys
import time
import glob

# Ensure we can import from backend
sys.path.append(os.getcwd())

from backend.services.backup_service import perform_backup

def test_backup_rotation():
    """Test that only the last 10 backups are kept for each database."""
    test_backup_dir = "test_backups"
    test_max_backups = 10
    
    # Clean up any existing test backups
    if os.path.exists(test_backup_dir):
        import shutil
        shutil.rmtree(test_backup_dir)
    
    print(f"Testing backup rotation (max {test_max_backups} backups)...\n")
    
    # Create 15 backups to test rotation
    for i in range(15):
        print(f"Creating backup {i+1}/15...", end=" ")
        perform_backup(
            db_files=["finance_tracker.db"],
            backup_dir=test_backup_dir,
            max_backups=test_max_backups
        )
        # Count current backups
        pattern = os.path.join(test_backup_dir, f"finance_tracker.db_*.bak")
        current_count = len(glob.glob(pattern))
        print(f"(Total backups: {current_count})")
        time.sleep(0.05)  # Small delay to ensure different timestamps
    
    # Final count
    pattern = os.path.join(test_backup_dir, f"finance_tracker.db_*.bak")
    backups = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULT:")
    print(f"{'='*60}")
    print(f"Expected backups: {test_max_backups}")
    print(f"Actual backups: {len(backups)}")
    status = "PASS" if len(backups) == test_max_backups else "FAIL"
    print(f"Status: {status}")
    
    # Cleanup
    print(f"\nCleaning up test directory: {test_backup_dir}")
    import shutil
    shutil.rmtree(test_backup_dir)
    print("Test completed!")

if __name__ == "__main__":
    test_backup_rotation()
