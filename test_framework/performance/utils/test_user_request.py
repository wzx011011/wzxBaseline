#!/usr/bin/env python3
"""
Test script to verify create_table with user's exact request format.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from test_framework.performance.utils.feishu_downloader import FeishuDownloader, load_feishu_config


def main():
    """Main function."""
    print("=== Testing FeishuDownloader.create_table with user's request format ===")
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
        app_token="M9WDbtXTralb4vs0GwKcNLD7nnc",  # Use the working app_token
        table_id=config['table_id']
    )
    
    # Use user's exact request format
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_table_name = f"test_table_{timestamp}"
    
    user_fields = [
        {
            "type": 1,
            "is_primary": True,
            "name": "name",
            "ui_type": "Text"  # 文本类型需指定 ui_type
        },
        {
            "type": 2,
            "name": "value",
            "ui_type": "Number"  # 数字类型需指定 ui_type
        },
        {
            "type": 4,
            "name": "status",
            "ui_type": "MultiSelect",  # 多选类型需指定 ui_type
            "property": {
                "options": [  # 必须定义选项
                    {"name": "Active", "id": "opt1", "color": 3},
                    {"name": "Inactive", "id": "opt2", "color": 5}
                ]
            }
        },
        {
            "type": 5,
            "name": "created_at",
            "ui_type": "DateTime"  # 日期类型需指定 ui_type
        }
    ]
    
    print(f"Testing table creation with name: {test_table_name}")
    print(f"Fields: {user_fields}")
    
    try:
        # Create the table using user's exact format
        table_id = downloader.create_table(test_table_name, user_fields)
        print(f"✓ Successfully created table: {test_table_name} with ID: {table_id}")
        
        # Verify the table was created
        retrieved_table_id = downloader.get_table_id_by_name(test_table_name)
        print(f"✓ Successfully retrieved table ID: {retrieved_table_id}")
        
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    print("=== Test Complete ===")


if __name__ == "__main__":
    main()