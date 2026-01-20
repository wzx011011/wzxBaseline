#!/usr/bin/env python3
"""
Simple test script to verify that create_table works.
"""

import sys
import os
import requests
import json
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from test_framework.performance.utils.feishu_downloader import load_feishu_config, BASE_URL

def load_env_file():
    """Load environment variables from .env file if it exists."""
    from dotenv import load_dotenv
    dotenv_path = Path(project_root) / ".env"
    if dotenv_path.exists():
        print(f"Loading env from {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path)

def get_access_token(app_id, app_secret):
    """Get Feishu access token."""
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret,
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to get tenant access token: {data}")
    return data["tenant_access_token"]

def main():
    """Main function to test create_table."""
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
    
    # Test direct API call with exact payload
    print("Testing direct API call with exact payload...")
    
    # Get access token
    access_token = get_access_token(config['app_id'], config['app_secret'])
    
    # Use the app_token from configuration instead of hardcoded one
    app_token = config['app_token']
    
    # Create the exact payload from the successful example
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_table_name = f"test_table_{timestamp}"
    
    # Create a very simple payload with only one text field
    payload = {
        "name": test_table_name,
        "fields": [
            {
                "type": 1,
                "is_primary": True,
                "name": "name",
                "ui_type": "Text"
            }
        ]
    }
    
    print(f"Creating table with payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    # Make the API call
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"Response status: {resp.status_code}")
        print(f"Response content: {resp.text}")
        resp.raise_for_status()
        
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Create table failed: {data}")
        
        table_id = data.get("data", {}).get("table_id")
        print(f"✓ Successfully created table: {test_table_name} with ID: {table_id}")
        
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=== Test Complete ===")


if __name__ == "__main__":
    main()