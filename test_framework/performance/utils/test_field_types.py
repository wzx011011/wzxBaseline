#!/usr/bin/env python3
"""
Test script to verify that create_table works with numeric field types.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from test_framework.performance.utils.feishu_downloader import FeishuDownloader, load_feishu_config

def main():
    """Test create_table with numeric field types."""
    print("=== Testing Numeric Field Types ===")
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
    
    # Test create_table with numeric field types
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_table_name = f"test_field_types_{timestamp}"
    
    print(f"Testing create_table with numeric field types for table: {test_table_name}")
    
    # Define table fields with numeric types
    # Feishu API field types:
    # 1: Text, 2: Number, 3: Single select, 4: Checkbox, 5: Date
    fields = [
        {"name": "name", "type": 1},       # Text
        {"name": "value", "type": 2},      # Number
        {"name": "status", "type": 4},     # Checkbox
        {"name": "created_at", "type": 5}  # Date
    ]
    
    try:
        # Try to create the table with numeric field types
        table_id = downloader.create_table(test_table_name, fields)
        print(f"✓ Successfully created table: {test_table_name} with ID: {table_id}")
        
        # Verify the table was created
        retrieved_table_id = downloader.get_table_id_by_name(test_table_name)
        print(f"✓ Successfully retrieved created table with ID: {retrieved_table_id}")
        
        if retrieved_table_id == table_id:
            print(f"✓ Table ID matches, creation successful!")
            print("✓ Numeric field types are working correctly!")
        else:
            print(f"✗ Table ID mismatch: created={table_id}, retrieved={retrieved_table_id}")
            
    except Exception as e:
        print(f"✗ Error during table creation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    finally:
        # Clean up: try to delete the test table if it was created
        try:
            if 'table_id' in locals():
                from test_list_tables import test_delete_table
                test_delete_table(downloader, table_id)
                print(f"✓ Successfully deleted test table: {test_table_name}")
        except Exception as e:
            print(f"✗ Error deleting test table: {e}")
    
    print()
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()
