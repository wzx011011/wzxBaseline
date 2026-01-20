#!/usr/bin/env python3
"""
Test script to verify that a simple table can be created in Feishu Bitable.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from test_framework.performance.utils.feishu_downloader import FeishuDownloader, load_feishu_config

def main():
    """Test creating a simple table with minimal fields."""
    print("=== Testing Simple Table Creation ===")
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
    
    # Initialize FeishuDownloader with the correct app_token provided by user
    downloader = FeishuDownloader(
        app_id=config['app_id'],
        app_secret=config['app_secret'],
        app_token="M9WDbtXTralb4vs0GwKcNLD7nnc",
        table_id=config['table_id']
    )
    
    # Test creating a very simple table with just one field
    from datetime import datetime
    current_date = datetime.now().strftime("%Y%m%d")
    test_table_name = f"simple_test_{current_date}"
    
    print(f"Testing simple table creation for: {test_table_name}...")
    
    # Define just one field - the minimal required
    test_fields = [
        {"field_name": "test_field", "type": 1, "property": {}}  # Text field with empty property
    ]
    
    table_id = None
    try:
        # Create the test table
        table_id = downloader.create_table(test_table_name, test_fields)
        print(f"✓ Successfully created test table: {test_table_name} with ID: {table_id}")
        
        # Verify the table was created
        retrieved_table_id = downloader.get_table_id_by_name(test_table_name)
        print(f"✓ Successfully retrieved created table with ID: {retrieved_table_id}")
        
        if retrieved_table_id == table_id:
            print(f"✓ Table ID matches, creation successful!")
        else:
            print(f"✗ Table ID mismatch: created={table_id}, retrieved={retrieved_table_id}")
            
    except Exception as e:
        print(f"✗ Error during table creation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    finally:
        # Clean up: try to delete the test table
        if table_id:
            try:
                from test_list_tables import test_delete_table
                test_delete_table(downloader, table_id)
                print(f"✓ Successfully deleted test table: {test_table_name}")
            except Exception as e:
                print(f"✗ Error deleting test table: {e}")
    
    print()
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()

