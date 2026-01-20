#!/usr/bin/env python3
"""
Raw test script to verify that create_table works using direct HTTP requests.
"""

import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

BASE_URL = "https://open.feishu.cn/open-apis"


def load_env_file():
    """Load environment variables from .env file if it exists."""
    dotenv_path = Path(project_root) / ".env"
    if dotenv_path.exists():
        print(f"Loading env from {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path)


def get_access_token(app_id, app_secret):
    """Get access token from Feishu API."""
    print(f"Getting access token for app_id: {app_id}")
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Get access token failed: {data}")
    
    return data.get("tenant_access_token")


def resolve_app_token_if_needed(access_token, app_token):
    """
    When app_token is a wiki token (from feishu.cn/wiki/xxx) or base token (from feishu.cn/base/xxx),
    use knowledge API to resolve it to the underlying bitable app_token.
    """
    print(f"Resolving app_token: {app_token}")
    
    # Already a bitable token
    if app_token.startswith("bascn"):
        print(f"App token {app_token} is already a bitable token")
        return app_token

    # Check if it's a base token (from feishu.cn/base/xxx) or already a valid app_token
    # First, try to use it directly as app_token
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        # If the request succeeds, it means this is already a valid app_token
        if resp.ok:
            print(f"App token {app_token} is already a valid app_token")
            return app_token
    except Exception as e:
        print(f"Direct app_token access failed: {e}")
        # This is expected if the token is a wiki token or base token
    
    # Try to resolve as wiki token
    url = f"{BASE_URL}/wiki/v2/spaces/get_node"
    try:
        resp = requests.get(
            url,
            headers=headers,
            params={"token": app_token},
            timeout=10,
        )
        
        if resp.ok:
            payload = resp.json()
            data = payload.get("data", {}) if isinstance(payload, dict) else {}
            node = data.get("node", {}) if isinstance(data, dict) else {}
            obj_type = node.get("obj_type")
            obj_token = node.get("obj_token")
            
            if obj_type in ("bitable", 4) and obj_token:
                # This is a bitable node, use the obj_token as app_token
                print(f"Successfully resolved app_token to: {obj_token}")
                return obj_token
    except Exception as e:
        print(f"Wiki token resolve failed: {e}")
        # This is expected if the token is a base token
    
    # If all else fails, try to use it directly as app_token
    # This handles cases where the token is a base token from feishu.cn/base/xxx
    print(f"All token resolution methods failed, trying to use token directly as app_token: {app_token}")
    return app_token


def create_table_raw(app_id, app_secret, app_token, table_name, fields):
    """Create table using raw HTTP request."""
    # Get access token
    access_token = get_access_token(app_id, app_secret)
    print(f"Got access token: {access_token[:20]}...")
    
    # Resolve app_token if needed
    resolved_app_token = resolve_app_token_if_needed(access_token, app_token)
    
    # Create table
    url = f"{BASE_URL}/bitable/v1/apps/{resolved_app_token}/tables"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    payload = {
        "name": table_name,
        "fields": fields
    }
    
    print(f"Sending request to: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    print(f"Response status: {resp.status_code}")
    print(f"Response body: {resp.text}")
    
    resp.raise_for_status()
    
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Create table failed: {data}")
    
    return data.get("data", {}).get("table_id")


def main():
    """Main function to test create_table."""
    print("=== Testing Feishu Bitable Create Table API ===")
    print()
    
    # Load environment variables from .env file
    load_env_file()
    
    # Get Feishu configuration from environment variables
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    app_token = "M9WDbtXTralb4vs0GwKcNLD7nnc"  # Use the same app_token as in test_slice.py
    
    if not app_id or not app_secret:
        print("ERROR: Feishu configuration not found in environment variables.")
        print("Please set: FEISHU_APP_ID, FEISHU_APP_SECRET")
        sys.exit(1)
    
    print("Feishu Configuration:")
    print(f"  App ID: {app_id}")
    print(f"  App Secret: {'*' * len(app_secret)}")
    print(f"  App Token: {app_token}")
    print()
    
    # Generate test table name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_table_name = f"test_table_{timestamp}"
    
    print(f"Testing create_table with table name: {test_table_name}")
    
    # Define table fields - use field_name as in test_slice.py
    # Feishu API field types:
    # 1: Text, 2: Number, 3: Single select, 4: Checkbox, 5: Date
    test_fields = [
        {"field_name": "file", "type": 1},
        {"field_name": "import_ms", "type": 2},
        {"field_name": "export_ms", "type": 2}
    ]
    
    try:
        # Try to create the table
        print(f"Creating table with fields: {test_fields}")
        table_id = create_table_raw(app_id, app_secret, app_token, test_table_name, test_fields)
        print(f"✓ Successfully created table: {test_table_name} with ID: {table_id}")
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=== Test Complete ===")


if __name__ == "__main__":
    main()