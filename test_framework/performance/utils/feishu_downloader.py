import os
import json
import time
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

# Base URL for Feishu API
BASE_URL = "https://open.feishu.cn/open-apis"

def _parse_feishu_table_url(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    path = parsed.path or ""
    path = path.strip("/")
    if not path:
        return None
    parts = path.split("/")
    token = parts[-1]
    return token or None


def load_feishu_config() -> Optional[Dict[str, str]]:
    required_keys = ["app_id", "app_secret", "table_id"]
    cfg = {}
    
    env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
    
    for key in required_keys:
        env_key = f"FEISHU_{key.upper()}"
        if env_key in os.environ:
            cfg[key] = os.environ[env_key]
        else:
            return None
    
    table_url_env = "FEISHU_TABLE_URL"
    app_token = None
    if table_url_env in os.environ:
        app_token = _parse_feishu_table_url(os.environ[table_url_env])
    if not app_token and "FEISHU_APP_TOKEN" in os.environ:
        app_token = os.environ["FEISHU_APP_TOKEN"]
    if not app_token:
        return None
    cfg["app_token"] = app_token
    
    for key in ["view_id", "file_field", "download_dir"]:
        env_key = f"FEISHU_{key.upper()}"
        if env_key in os.environ:
            cfg[key] = os.environ[env_key]
    
    return cfg

class FeishuDownloader:
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        app_token: str,
        table_id: str,
        view_id: Optional[str] = None,
        file_field: str = "文件",
        download_dir: Optional[Path] = None,
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        self.table_id = table_id
        self.view_id = view_id
        self.file_field = file_field
        self.download_dir = download_dir or Path("artifacts") / "feishu_3mf"
        self._access_token = None
        self._access_token_expires = 0
        self._resolved_app_token = None
        # Initialize logger
        self.logger = logging.getLogger(__name__)
    
    def _ensure_token(self):
        """
        Ensure we have a valid access token.
        """
        if not self._access_token or time.time() > self._access_token_expires:
            self._refresh_token()
    
    def _refresh_token(self):
        """
        Refresh the access token.
        """
        url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Failed to get tenant access token: {data}")
        self._access_token = data["tenant_access_token"]
        self._access_token_expires = time.time() + data["expire"] - 60  # Refresh 1 minute before expiry
    
    def _headers(self) -> Dict[str, str]:
        """
        Get headers with access token.
        """
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json; charset=utf-8",
        }
    
    def _get_with_retry(self, url: str, headers: Dict[str, str], params: Dict[str, Any] = None, timeout: int = 30) -> requests.Response:
        """
        Make a GET request with retry.
        """
        max_retries = 3
        retry_delay = 2
        
        last_error = None
        last_status_code = None
        last_response_text = None
        
        for i in range(max_retries):
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=timeout)
                if resp.ok:
                    return resp
                # If we got an HTTP error, save the details
                last_status_code = resp.status_code
                last_response_text = resp.text
                last_error = f"HTTP {resp.status_code}: {resp.text}"
                print(f"Attempt {i+1}/{max_retries} failed with status {resp.status_code}: {resp.text}")
            except Exception as e:
                last_error = str(e)
                print(f"Attempt {i+1}/{max_retries} failed with exception: {e}")
            
            # Don't retry on certain error codes that are unlikely to succeed on retry
            if last_status_code in [400, 401, 403, 404, 405]:
                break
            
            time.sleep(retry_delay)
        
        # Raise a more informative error
        if last_status_code:
            raise RuntimeError(f"Max retries exceeded. Last error: HTTP {last_status_code}: {last_response_text}")
        else:
            raise RuntimeError(f"Max retries exceeded. Last error: {last_error}")
    
    def _post_with_retry(self, url: str, headers: Dict[str, str], json: Dict[str, Any] = None, timeout: int = 30) -> requests.Response:
        """
        Make a POST request with retry.
        """
        max_retries = 3
        retry_delay = 2
        
        last_error = None
        last_status_code = None
        last_response_text = None
        
        for i in range(max_retries):
            try:
                resp = requests.post(url, headers=headers, json=json, timeout=timeout)
                if resp.ok:
                    return resp
                # If we got an HTTP error, save the details
                last_status_code = resp.status_code
                last_response_text = resp.text
                last_error = f"HTTP {resp.status_code}: {resp.text}"
                print(f"Attempt {i+1}/{max_retries} failed with status {resp.status_code}: {resp.text}")
            except Exception as e:
                last_error = str(e)
                print(f"Attempt {i+1}/{max_retries} failed with exception: {e}")
            
            # Don't retry on certain error codes that are unlikely to succeed on retry
            if last_status_code in [400, 401, 403, 404, 405]:
                break
            
            time.sleep(retry_delay)
        
        # Raise a more informative error
        if last_status_code:
            raise RuntimeError(f"Max retries exceeded. Last error: HTTP {last_status_code}: {last_response_text}")
        else:
            raise RuntimeError(f"Max retries exceeded. Last error: {last_error}")
    
    def _resolve_app_token_if_needed(self) -> str:
        """
        When FEISHU_APP_TOKEN is a wiki token (from feishu.cn/wiki/xxx) or base token (from feishu.cn/base/xxx),
        use knowledge API to resolve it to the underlying bitable app_token.
        """
        if self._resolved_app_token:
            return self._resolved_app_token
        # Already a bitable token
        if self.app_token.startswith("bascn"):
            self._resolved_app_token = self.app_token
            return self._resolved_app_token

        self._ensure_token()
        # Check if it's a base token (from feishu.cn/base/xxx) or already a valid app_token
        # First, try to use it directly as app_token and verify response code == 0
        url = f"{BASE_URL}/bitable/v1/apps/{self.app_token}/tables"
        try:
            resp = self._get_with_retry(
                url,
                headers=self._headers(),
                timeout=10,
            )
            if resp.ok:
                payload = resp.json()
                if isinstance(payload, dict) and payload.get("code") == 0:
                    self._resolved_app_token = self.app_token
                    return self._resolved_app_token
        except Exception as e:
            print(f"Direct app_token access failed: {e}")
            # This is expected if the token is a wiki token or base token
        
        # Try to resolve as wiki token
        url = f"{BASE_URL}/wiki/v2/spaces/get_node"
        try:
            resp = self._get_with_retry(
                url,
                headers=self._headers(),
                params={"token": self.app_token},
                timeout=10,
            )
            
            if resp.ok:
                payload = resp.json()
                if isinstance(payload, dict) and payload.get("code") == 0:
                    data = payload.get("data", {})
                    node = data.get("node", {}) if isinstance(data, dict) else {}
                    obj_type = node.get("obj_type")
                    obj_token = node.get("obj_token")
                    if obj_type in ("bitable", 4) and obj_token:
                        self._resolved_app_token = obj_token
                        return self._resolved_app_token
        except Exception as e:
            print(f"Wiki token resolve failed: {e}")
            # This is expected if the token is a base token
        
        # If all else fails, try to use it directly as app_token
        # This handles cases where the token is a base token from feishu.cn/base/xxx
        print(f"All token resolution methods failed, trying to use token directly as app_token: {self.app_token}")
        self._resolved_app_token = self.app_token
        return self._resolved_app_token
    
    def get_table_id_by_name(self, table_name: str) -> str:
        """
        Get table ID by table name.
        """
        self._ensure_token()
        app_token = self._resolve_app_token_if_needed()
        
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
        resp = self._get_with_retry(url, headers=self._headers(), timeout=20)
        resp.raise_for_status()
        
        payload = resp.json()
        if payload.get("code") != 0:
            raise RuntimeError(f"Get tables failed: {payload}")
        
        tables = payload.get("data", {}).get("items", [])
        self.logger.info(f"Retrieved {len(tables)} tables from app_token: {app_token}")
        
        # Log all table names for debugging
        table_names = [table.get("name", "") for table in tables]
        self.logger.info(f"Available table names: {table_names}")
        
        # Use case-insensitive comparison to find the table
        for table in tables:
            current_name = table.get("name", "")
            if current_name.lower() == table_name.lower():
                table_id = table.get("table_id")
                self.logger.info(f"Found table '{table_name}' (case-insensitive match for '{current_name}') with ID: {table_id}")
                return table_id
        
        raise RuntimeError(f"Table '{table_name}' not found. Available tables: {table_names}")
    
    def create_table(self, table_name: str, fields: List[Dict[str, Any]]) -> str:
        """
        Create a new table in the Feishu Bitable.
        """
        self._ensure_token()
        app_token = self._resolve_app_token_if_needed()
        
        # Convert field_name to name for Feishu API compatibility and add required ui_type
        api_fields = []
        for field in fields:
            api_field = field.copy()
            
            # Convert field_name to name if needed
            if "field_name" in api_field and "name" not in api_field:
                api_field["name"] = api_field.pop("field_name")
            
            # Add required ui_type based on field type
            field_type = api_field.get("type")
            if field_type == 1 and "ui_type" not in api_field:
                api_field["ui_type"] = "Text"  # Text type
            elif field_type == 2 and "ui_type" not in api_field:
                api_field["ui_type"] = "Number"  # Number type
            elif field_type == 3 and "ui_type" not in api_field:
                api_field["ui_type"] = "SingleSelect"  # Single select type
            elif field_type == 4 and "ui_type" not in api_field:
                api_field["ui_type"] = "MultiSelect"  # Multi select/Checkbox type
            elif field_type == 5 and "ui_type" not in api_field:
                api_field["ui_type"] = "DateTime"  # Date type
            
            # For multi-select fields (type 4), add default options if not provided
            if field_type == 4 and "property" not in api_field:
                api_field["property"] = {
                    "options": [
                        {"name": "Option 1", "id": "opt1", "color": 3},
                        {"name": "Option 2", "id": "opt2", "color": 5}
                    ]
                }
            
            api_fields.append(api_field)
        
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
        payload = {
            "name": table_name,
            "fields": api_fields
        }
        
        # Add debug information
        print(f"DEBUG: Creating table with payload: {payload}")
        
        resp = self._post_with_retry(url, headers=self._headers(), json=payload, timeout=20)
        resp.raise_for_status()
        
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Create table failed: {data}")
        
        return data.get("data", {}).get("table_id")
    
    def add_records(self, table_id: str, records: List[Dict[str, Any]]) -> None:
        """
        Add multiple records to a table.
        """
        self._ensure_token()
        app_token = self._resolve_app_token_if_needed()
        
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        
        # Prepare records for Feishu API - use simple field values, not complex structures
        feishu_records = []
        for record in records:
            # For each record, use simple key-value pairs
            feishu_records.append({
                "fields": record  # Directly use the record as fields, no conversion needed
            })
        
        payload = {
            "records": feishu_records
        }
        
        resp = self._post_with_retry(url, headers=self._headers(), json=payload, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Add records failed: {data}")
    
    def download_all(self) -> List[Dict[str, str]]:
        """
        Download all 3MF files from the Feishu table.
        """
        self._ensure_token()
        app_token = self._resolve_app_token_if_needed()
        
        # Get all records from the table
        records = self._get_all_records_from_table()
        
        # Download files from each record
        downloaded_files = []
        for record in records:
            record_id = record.get("record_id") or ""
            file_info = record.get("fields", {}).get(self.file_field, {})
            
            # Handle case where file_info is an array (multiple files in one field)
            if isinstance(file_info, list):
                for file_item in file_info:
                    if isinstance(file_item, dict) and "url" in file_item:
                        file_url = file_item["url"]
                        file_name = file_item.get("name", "unknown.3mf")
                        
                        # Ensure download directory exists
                        self.download_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Download the file
                        file_path = self.download_dir / file_name
                        try:
                            self._download_file(file_url, file_path)
                            downloaded_files.append(
                                {
                                    "path": str(file_path),
                                    "name": file_name,
                                    "record_id": record_id,
                                }
                            )
                        except Exception as e:
                            self.logger.error(f"Failed to download file {file_name} from URL {file_url}: {e}")
            # Handle case where file_info is a single file object
            elif isinstance(file_info, dict) and "url" in file_info:
                file_url = file_info["url"]
                file_name = file_info.get("name", "unknown.3mf")
                
                # Ensure download directory exists
                self.download_dir.mkdir(parents=True, exist_ok=True)
                
                # Download the file
                file_path = self.download_dir / file_name
                try:
                    self._download_file(file_url, file_path)
                    downloaded_files.append(
                        {
                            "path": str(file_path),
                            "name": file_name,
                            "record_id": record_id,
                        }
                    )
                except Exception as e:
                    self.logger.error(f"Failed to download file {file_name} from URL {file_url}: {e}")
        
        return downloaded_files
    
    def _get_all_records_from_table(self) -> List[Dict[str, Any]]:
        """
        Get all records from the Feishu table.
        """
        self._ensure_token()
        app_token = self._resolve_app_token_if_needed()
        
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{self.table_id}/records"
        headers = self._headers()
        
        all_records = []
        page_token = None
        
        while True:
            params = {"page_size": 100}
            if page_token:
                params["page_token"] = page_token
            
            resp = self._get_with_retry(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(f"Failed to get records: {data}")
            
            records = data.get("data", {}).get("items", [])
            all_records.extend(records)
            
            page_token = data.get("data", {}).get("page_token")
            if not page_token:
                break
        
        return all_records
    
    def _download_file(self, url: str, file_path: Path):
        """
        Download a file from the given URL to the specified path.
        If the file already exists locally, it won't be downloaded again.
        """
        # Check if the file already exists
        if file_path.exists():
            self.logger.info(f"File already exists, skipping download: {file_path}")
            return
        
        headers = self._headers()
        
        with self._get_with_retry(url, headers=headers, timeout=60) as resp:
            resp.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
