#!/usr/bin/env python3
"""
Test script to create a table with correct field format.
"""

import requests
import json
from datetime import datetime
import os

# Load environment variables
from test_list_tables import load_env_file
load_env_file()

# Get app_id and app_secret from environment variables
app_id = os.environ.get('FEISHU_APP_ID')
app_secret = os.environ.get('FEISHU_APP_SECRET')
if not app_id or not app_secret:
    print("ERROR: Missing FEISHU_APP_ID or FEISHU_APP_SECRET in environment variables")
    exit(1)

# User-provided app_token
app_token = "M9WDbtXTralb4vs0GwKcNLD7nnc"
BASE_URL = "https://open.feishu.cn/open-apis"

def get_access_token():
    """Get access token from Feishu API."""
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get('tenant_access_token')
    else:
        print(f"ERROR: Failed to get access token: {response.text}")
        exit(1)

def create_table_correct(access_token, table_name, fields):
    """Create table with correct field format."""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "name": table_name,
        "fields": fields
    }
    
    print(f"DEBUG: Request URL: {url}")
    print(f"DEBUG: Request Headers: {headers}")
    print(f"DEBUG: Request Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"DEBUG: Response Status Code: {response.status_code}")
    print(f"DEBUG: Response Content: {response.text}")
    
    return response

def main():
    """Main function."""
    print("=== Testing Table Creation with Correct Field Format ===")
    print()
    
    # Get access token
    access_token = get_access_token()
    print(f"✓ Successfully obtained access token")
    print()
    
    # Generate test table name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_table_name = f"test_correct_format_{timestamp}"
    
    print(f"Testing table creation with name: {test_table_name}")
    print()
    
    # Define table fields with correct format
    # Based on the existing table's fields, we need:
    # - field_name for field name
    # - type for field type (numeric)
    # - is_primary to indicate primary key (at least one field must be true)
    fields = [
        {
            "field_name": "record_id",
            "type": 1,  # Text
            "is_primary": True  # Must have at least one primary key field
        },
        {
            "field_name": "file",
            "type": 1,  # Text
            "is_primary": False
        },
        {
            "field_name": "import_ms",
            "type": 2,  # Number
            "is_primary": False
        }
    ]
    
    # Create table with correct field format
    print("=== Creating Table with Correct Field Format ===")
    response = create_table_correct(access_token, test_table_name, fields)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            table_id = data.get('data', {}).get('table_id')
            print(f"✓ Successfully created table: {test_table_name} with ID: {table_id}")
        else:
            print(f"✗ API returned error: {data.get('msg')}")
    else:
        print(f"✗ HTTP request failed: {response.status_code}")
    
    print()
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()