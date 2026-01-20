#!/usr/bin/env python3
"""
Test script to get fields of an existing table.
"""

import requests
import json
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

# User-provided app_token and existing table_id
app_token = "M9WDbtXTralb4vs0GwKcNLD7nnc"
table_id = "tbl8KJ3EashxIwQW"  # From test_log-1 table
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

def get_table_fields(access_token):
    """Get fields of an existing table."""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    print(f"DEBUG: Request URL: {url}")
    print(f"DEBUG: Request Headers: {headers}")
    
    response = requests.get(url, headers=headers)
    print(f"DEBUG: Response Status Code: {response.status_code}")
    print(f"DEBUG: Response Content: {response.text}")
    
    return response

def main():
    """Main function."""
    print("=== Testing Table Fields Retrieval ===")
    print()
    
    # Get access token
    access_token = get_access_token()
    print(f"✓ Successfully obtained access token")
    print()
    
    # Get table fields
    print(f"=== Getting Fields for Table ID: {table_id} ===")
    response = get_table_fields(access_token)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            fields = data.get('data', {}).get('items', [])
            print(f"✓ Successfully retrieved {len(fields)} fields")
            print("Table Fields:")
            print("--------------------------------------------------")
            for field in fields:
                field_name = field.get('field_name', field.get('name', 'N/A'))
                field_type = field.get('type')
                print(f"  - {field_name} (Type: {field_type})")
                print(f"    Full field info: {json.dumps(field, indent=2, ensure_ascii=False)}")
                print("--------------------------------------------------")
        else:
            print(f"✗ API returned error: {data.get('msg')}")
    else:
        print(f"✗ HTTP request failed: {response.status_code}")
    
    print()
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()