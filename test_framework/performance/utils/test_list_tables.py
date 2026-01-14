import json
import os
from pathlib import Path
from feishu_downloader import FeishuDownloader, load_feishu_config, BASE_URL

def load_env_file():
    """
    Lightweight .env loader (no external dependency).
    Only sets keys that are not already in os.environ.
    """
    env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    print(f"Loading env from {env_path}")
    if not env_path.exists():
        print(f"Warning: .env file not found at {env_path}")
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val

def list_all_tables(downloader):
    """
    List all tables in the Feishu Bitable.
    """
    try:
        # Ensure we have a valid token
        downloader._ensure_token()
        
        # Resolve app token if needed
        app_token = downloader._resolve_app_token_if_needed()
        
        # Get all tables in the bitable
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
        headers = downloader._headers()
        
        resp = downloader._get_with_retry(url, headers=headers, timeout=20)
        resp.raise_for_status()
        
        payload = resp.json()
        if payload.get("code") != 0:
            raise RuntimeError(f"Get tables failed: {payload}")
        
        tables = payload.get("data", {}).get("items", [])
        
        print(f"✓ Successfully retrieved tables from Feishu Bitable")
        print(f"Total tables found: {len(tables)}")
        print()
        print("Table List:")
        print("-" * 50)
        
        for i, table in enumerate(tables, 1):
            table_name = table.get("name", "Unknown")
            table_id = table.get("table_id", "Unknown")
            revision = table.get("revision", "Unknown")
            
            print(f"{i}. Name: {table_name}")
            print(f"   ID: {table_id}")
            print(f"   Revision: {revision}")
            print("-" * 50)
        
        return tables
        
    except Exception as e:
        print(f"✗ Error listing tables: {e}")
        print("This might indicate insufficient permissions for the Feishu app.")
        print("Please check:")
        print("1. Feishu app has 'Bitable' API permissions")
        print("2. App token and table ID are correct")
        print("3. Environment variables are properly set")
        print(f"\nDetailed error: {str(e)}")
        return []

def test_create_table(downloader):
    """
    Test creating a new table in the Feishu Bitable.
    """
    try:
        # Generate a unique table name with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"test_table_{timestamp}"
        
        # Define table fields
        fields = [
            {"name": "name", "type": "text"},
            {"name": "value", "type": "number"},
            {"name": "status", "type": "checkbox"},
            {"name": "created_at", "type": "date"}
        ]
        
        print(f"\n=== Testing Table Creation ===")
        print(f"Creating table: {table_name}")
        print(f"Fields: {fields}")
        
        # Create the table
        table_id = downloader.create_table(table_name, fields)
        
        print(f"✓ Successfully created table: {table_name}")
        print(f"  Table ID: {table_id}")
        print("✓ Table creation permission verified")
        
        return table_name, table_id
        
    except Exception as e:
        print(f"\n✗ Error creating table: {e}")
        print("This might indicate insufficient permissions for creating tables.")
        print("Please check if the Feishu app has 'Create Table' permission.")
        print(f"\nDetailed error: {str(e)}")
        return None, None

def test_delete_table(downloader, table_id):
    """
    Test deleting a table in the Feishu Bitable.
    """
    try:
        print(f"\n=== Testing Table Deletion ===")
        print(f"Deleting table with ID: {table_id}")
        
        # Ensure we have a valid token
        downloader._ensure_token()
        
        # Resolve app token if needed
        app_token = downloader._resolve_app_token_if_needed()
        
        # Delete the table
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}"
        headers = downloader._headers()
        headers["Content-Type"] = "application/json"
        
        # Use session directly to send DELETE request
        resp = downloader.session.delete(url, headers=headers, timeout=20)
        
        if resp.status_code == 200:
            payload = resp.json()
            if payload.get("code") == 0:
                print(f"✓ Successfully deleted table: {table_id}")
                return True
            else:
                print(f"✗ Failed to delete table: {payload}")
        else:
            print(f"✗ Failed to delete table: HTTP {resp.status_code} {resp.reason}; body={resp.text}")
        
        return False
        
    except Exception as e:
        print(f"\n✗ Error deleting table: {e}")
        print(f"Detailed error: {str(e)}")
        return False

def test_add_record(downloader):
    """
    Test adding a record to the test_log table.
    """
    try:
        print(f"\n=== Testing Record Addition ===")
        print(f"Adding record to test_log table")
        
        # First, let's debug get_table_id_by_name method
        print("Debugging get_table_id_by_name method...")
        
        # Ensure we have a valid token
        downloader._ensure_token()
        
        # Resolve app token if needed
        app_token = downloader._resolve_app_token_if_needed()
        
        # Get all tables to debug
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
        headers = downloader._headers()
        
        resp = downloader._get_with_retry(url, headers=headers, timeout=20)
        resp.raise_for_status()
        
        payload = resp.json()
        tables = payload.get("data", {}).get("items", [])
        
        print(f"Available tables: {[table.get('name') for table in tables]}")
        
        # Try to find test_log table manually
        test_log_table = None
        for table in tables:
            if table.get('name') == "test_log":
                test_log_table = table
                break
        
        if not test_log_table:
            print(f"✗ test_log table not found in available tables")
            return False
        
        test_log_table_id = test_log_table.get('table_id')
        print(f"Found test_log table with ID: {test_log_table_id}")
        
        # Generate test data
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Define test records (only include fields that should exist in the table)
        test_records = [
            {
                "name": "test_record",
                "created_at": current_time
            }
        ]
        
        # Add records to test_log table
        downloader.add_records(test_log_table_id, test_records)
        
        print(f"✓ Successfully added {len(test_records)} record(s) to test_log table")
        print("✓ Record addition permission verified")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error adding record: {e}")
        print("This might indicate insufficient permissions for adding records.")
        print("Please check if the Feishu app has 'Add Records' permission.")
        print(f"\nDetailed error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Main test function to list tables, test table creation, and test record addition.
    """
    print("=== Feishu Bitable Table List Test ===")
    print()
    
    # Load Feishu configuration from .env file
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
    
    # Step 1: List all tables
    existing_tables = list_all_tables(downloader)
    
    # Step 2: Test adding record to test_log table
    test_add_record(downloader)
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
