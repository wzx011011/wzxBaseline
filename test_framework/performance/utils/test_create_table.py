#!/usr/bin/env python3
"""
Test script to verify that create_table works.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from test_framework.performance.utils.feishu_downloader import FeishuDownloader, load_feishu_config, BASE_URL


def load_env_file():
    """Load environment variables from .env file if it exists."""
    from dotenv import load_dotenv
    dotenv_path = Path(project_root) / ".env"
    if dotenv_path.exists():
        print(f"Loading env from {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path)


def test_create_table(downloader):
    """Test create_table method."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_table_name = f"test_log_{timestamp}_test"
    
    print(f"Testing create_table with table name: {test_table_name}")
    
    # Define table fields - use field_name as required by Feishu API
    # Feishu API field types:
    # 1: Text, 2: Number, 3: Single select, 4: Checkbox, 5: Date
    test_fields = [
        {"field_name": "record_id", "type": 1},
        {"field_name": "file", "type": 1},
        {"field_name": "import_ms", "type": 2},
        {"field_name": "slice_ms", "type": 2},
        {"field_name": "export_ms", "type": 2},
        {"field_name": "import_ok", "type": 1},
        {"field_name": "slice_ok", "type": 1},
        {"field_name": "export_ok", "type": 1},
        {"field_name": "crashed", "type": 1},
        {"field_name": "error", "type": 1},
        {"field_name": "gcode_path", "type": 1}
    ]
    
    try:
        # Try to create the table
        table_id = downloader.create_table(test_table_name, test_fields)
        print(f"✓ Successfully created table: {test_table_name} with ID: {table_id}")
        return table_id
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_table_id_by_name(downloader, table_name):
    """Test get_table_id_by_name method."""
    try:
        table_id = downloader.get_table_id_by_name(table_name)
        print(f"✓ Successfully retrieved table ID: {table_id} for table name: {table_name}")
        return table_id
    except Exception as e:
        print(f"✗ Error retrieving table ID: {e}")
        return None


def main():
    """Main function."""
    print("=== Testing FeishuDownloader.create_table ===")
    print()
    
    # Load Feishu configuration
    config = load_feishu_config()
    if not config:
        print("ERROR: Feishu configuration not found in environment variables.")
        print("Please set: FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_APP_TOKEN, FEISHU_TABLE_ID")
        sys.exit(1)
    
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
    
    # Generate a unique table name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_table_name = f"test_table_{timestamp}"
    
    # Define simple table fields with proper primary key and ui_type
    test_fields = [
        {
            "field_name": "record_id",
            "type": 1,  # Text
            "is_primary": True,
            "ui_type": "Text"
        },
        {
            "field_name": "file",
            "type": 1,  # Text
            "ui_type": "Text"
        },
        {
            "field_name": "import_ms",
            "type": 2,  # Number
            "ui_type": "Number"
        }
    ]
    
    print(f"Testing table creation with name: {test_table_name}")
    print(f"Fields: {test_fields}")
    
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
        # Clean up: try to delete the test table if it was created
        if table_id:
            try:
                # Implement delete table functionality if needed
                print(f"✓ Test completed, table {test_table_name} with ID {table_id} created successfully")
            except Exception as e:
                print(f"✗ Error during cleanup: {e}")
    
    print()
    print("=== Test Complete ===")


if __name__ == "__main__":
    print("=== Testing FeishuDownloader.create_table ===")
    print()
    
    # Load environment variables from .env file
    load_env_file()
    
    # Load Feishu configuration from environment variables
    config = load_feishu_config()
    if not config:
        print("ERROR: Feishu configuration not found in environment variables.")
        print("Please set: FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_APP_TOKEN, FEISHU_TABLE_ID")
        sys.exit(1)
    
    print("Feishu Configuration:")
    print(f"  App ID: {config['app_id']}")
    print(f"  App Secret: {'*' * len(config['app_secret'])}")
    print(f"  App Token: {config['app_token']}")
    print(f"  Table ID: {config['table_id']}")
    print()
    
    # Initialize FeishuDownloader with explicit app_token
    downloader = FeishuDownloader(
        app_id=config['app_id'],
        app_secret=config['app_secret'],
        app_token="M9WDbtXTralb4vs0GwKcNLD7nnc",  # Use the same app_token as in test_slice.py
        table_id=config['table_id']
    )
    
    # Test create_table
    table_id = test_create_table(downloader)
    
    if table_id:
        # Test get_table_id_by_name
        test_get_table_id_by_name(downloader, os.path.basename(table_id.split('/')[-1]) if '/' in table_id else table_id)
    
    print()
print("=== Test Complete ===")