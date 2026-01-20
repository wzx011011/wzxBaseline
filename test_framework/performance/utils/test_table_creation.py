#!/usr/bin/env python3
"""
Test script to verify that write_report_to_feishu_after_tests handles missing test_log table correctly.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from test_framework.performance.utils.feishu_downloader import FeishuDownloader, load_feishu_config

def main():
    """Test the write_report_to_feishu_after_tests function's table creation logic."""
    print("=== Testing Test Log Table Creation Logic ===")
    print()
    
    # Load Feishu configuration from .env file
    from test_list_tables import load_env_file
    load_env_file()
    
    # Load Feishu configuration from environment variables
    config = load_feishu_config()
    if not config:
        print("ERROR: Feishu configuration not found in environment variables.")
        print("Please set: FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_APP_TOKEN, FEISHU_TABLE_ID")
        return
    
    print("Feishu Configuration:")
    print(f"  App ID: {config['app_id']}")
    print(f"  App Secret: {'*' * len(config['app_secret'])}")
    print(f"  App Token: {config['app_token']}")
    print(f"  Table ID: {config['table_id']}")
    print()
    
    # Initialize FeishuDownloader
    downloader = FeishuDownloader(
        app_id=config['app_id'],
        app_secret=config['app_secret'],
        app_token=config['app_token'],
        table_id=config['table_id']
    )
    
    # Test the table creation logic with a non-existent table name
    print("Testing table creation logic...")
    
    from datetime import datetime
    current_date = datetime.now().strftime("%Y%m%d")
    test_table_name = f"test_log_nonexistent_{current_date}"
    print(f"Testing with non-existent table: {test_table_name}")
    
    # Define simple table fields
    table_fields = [
        {"name": "record_id", "type": "text"},
        {"name": "file", "type": "text"},
        {"name": "import_ms", "type": "number"},
        {"name": "slice_ms", "type": "number"},
        {"name": "export_ms", "type": "number"},
        {"name": "import_ok", "type": "text"},
        {"name": "slice_ok", "type": "text"},
        {"name": "export_ok", "type": "text"},
        {"name": "crashed", "type": "text"},
        {"name": "error", "type": "text"},
        {"name": "gcode_path", "type": "text"}
    ]
    
    try:
        # Try to get the non-existent table first
        print(f"1. Trying to get non-existent table: {test_table_name}")
        table_id = downloader.get_table_id_by_name(test_table_name)
        print(f"   ERROR: Table {test_table_name} should not exist, but got ID: {table_id}")
        return
    except RuntimeError as e:
        if "not found" in str(e).lower():
            print(f"   ✓ Correctly got 'not found' error for non-existent table")
        else:
            print(f"   ✗ Unexpected error: {e}")
            return
    
    print()
    print(f"2. Testing create_table method with simple fields...")
    
    try:
        # Try to create the table with simple fields
        table_id = downloader.create_table(test_table_name, table_fields)
        print(f"   ✓ Successfully created table: {test_table_name} with ID: {table_id}")
        
        # Verify the table was created
        print(f"3. Verifying table creation...")
        retrieved_table_id = downloader.get_table_id_by_name(test_table_name)
        print(f"   ✓ Successfully retrieved created table with ID: {retrieved_table_id}")
        
        if retrieved_table_id == table_id:
            print(f"   ✓ Table ID matches, creation successful!")
        else:
            print(f"   ✗ Table ID mismatch: created={table_id}, retrieved={retrieved_table_id}")
            
    except Exception as e:
        print(f"   ✗ Error during table creation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    finally:
        # Clean up: try to delete the test table if it was created
        try:
            if 'table_id' in locals():
                from test_list_tables import test_delete_table
                test_delete_table(downloader, table_id)
                print(f"4. ✓ Successfully deleted test table: {test_table_name}")
        except Exception as e:
            print(f"4. ✗ Error deleting test table: {e}")
    
    print()
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()
