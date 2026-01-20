#!/usr/bin/env python3
"""
Simple test script to create a table with minimal configuration.
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

def create_table_simple(access_token, table_name):
    """Create table with minimal configuration."""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    # Only provide table name, no custom fields
    payload = {
        "name": table_name
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
    print("=== Testing Simple Table Creation ===")
    print()
    
    # Get access token
    access_token = get_access_token()
    print(f"✓ Successfully obtained access token")
    print()
    
    # Generate test table name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_table_name = f"test_simple_{timestamp}"
    
    print(f"Testing table creation with name: {test_table_name}")
    print()
    
    # Test: Create table with only name, no custom fields
    print("=== Test: Create table with minimal configuration ===")
    response = create_table_simple(access_token, test_table_name)
    
    print()
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()