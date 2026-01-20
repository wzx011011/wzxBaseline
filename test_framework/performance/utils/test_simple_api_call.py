#!/usr/bin/env python3
"""
Simple test script to call Feishu API directly for table creation.
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

def create_table(access_token, table_name, fields):
    """Create table using Feishu API."""
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
    print("=== Testing Feishu API Direct Call ===")
    print()
    
    # Get access token
    access_token = get_access_token()
    print(f"✓ Successfully obtained access token")
    print()
    
    # Generate test table name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_table_name = f"test_direct_api_{timestamp}"
    
    print(f"Testing table creation with name: {test_table_name}")
    print()
    
    # Test 1: Using "field_name" and numeric types (as used in test_create_table.py)
    print("=== Test 1: Using 'field_name' and numeric types ===")
    fields1 = [
        {"field_name": "name", "type": 1},       # Text
        {"field_name": "value", "type": 2},      # Number
    ]
    
    response1 = create_table(access_token, test_table_name + "_1", fields1)
    print()
    
    # Test 2: Using "name" and string types (as used in test_table_creation.py)
    print("=== Test 2: Using 'name' and string types ===")
    fields2 = [
        {"name": "name", "type": "text"},       # Text
        {"name": "value", "type": "number"},    # Number
    ]
    
    response2 = create_table(access_token, test_table_name + "_2", fields2)
    print()
    
    # Test 3: Using "name" and numeric types (mixed)
    print("=== Test 3: Using 'name' and numeric types ===")
    fields3 = [
        {"name": "name", "type": 1},       # Text
        {"name": "value", "type": 2},      # Number
    ]
    
    response3 = create_table(access_token, test_table_name + "_3", fields3)
    print()
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()