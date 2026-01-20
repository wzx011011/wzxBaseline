#!/usr/bin/env python3
"""
Simple test script to list tables in a Feishu Bitable app.
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

def list_tables(access_token):
    """List tables in the Feishu Bitable app."""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
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
    print("=== Testing Table Listing ===")
    print()
    
    # Get access token
    access_token = get_access_token()
    print(f"✓ Successfully obtained access token")
    print()
    
    # List tables
    print("=== Listing Tables ===")
    response = list_tables(access_token)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            tables = data.get('data', {}).get('items', [])
            print(f"✓ Successfully retrieved {len(tables)} tables")
            for table in tables:
                print(f"  - {table.get('name')} (ID: {table.get('table_id')})")
        else:
            print(f"✗ API returned error: {data.get('msg')}")
    else:
        print(f"✗ HTTP request failed: {response.status_code}")
    
    print()
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()