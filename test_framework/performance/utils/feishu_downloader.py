import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import requests


BASE_URL = "https://open.feishu.cn/open-apis"


def load_feishu_config() -> Optional[Dict[str, str]]:
    """
    Load Feishu (Lark) app configuration from environment variables.
    Required:
        FEISHU_APP_ID
        FEISHU_APP_SECRET
        FEISHU_APP_TOKEN   # bitable app token (bascn...) or wiki token (wiki/xxx)
        FEISHU_TABLE_ID    # table id inside the bitable
    Optional:
        FEISHU_VIEW_ID     # view id to filter rows
        FEISHU_FILE_FIELD  # attachment field name, default '文件'
        FEISHU_DOWNLOAD_DIR
    """
    cfg = {
        "app_id": os.getenv("FEISHU_APP_ID"),
        "app_secret": os.getenv("FEISHU_APP_SECRET"),
        "app_token": os.getenv("FEISHU_APP_TOKEN"),
        "table_id": os.getenv("FEISHU_TABLE_ID"),
        "view_id": os.getenv("FEISHU_VIEW_ID"),
        "file_field": os.getenv("FEISHU_FILE_FIELD", "文件"),
        "download_dir": os.getenv("FEISHU_DOWNLOAD_DIR"),
    }
    print(cfg)
    required_keys = ("app_id", "app_secret", "app_token", "table_id")
    if any(not cfg[k] for k in required_keys):
        return None
    return cfg


class FeishuDownloader:
    """Tiny helper to pull 3MF attachments from a Feishu Bitable."""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        app_token: str,
        table_id: str,
        view_id: Optional[str] = None,
        file_field: str = "文件",
        download_dir: Union[Path, str] = Path("artifacts") / "feishu_3mf",
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token  # can be bascn... or wiki token
        self.table_id = table_id
        self.view_id = view_id
        self.file_field = file_field
        self.download_dir = Path(download_dir)
        self.manifest_path = self.download_dir / "downloads.json"
        self.session = requests.Session()
        self._tenant_token: Optional[str] = None
        self._resolved_app_token: Optional[str] = None
        self._manifest_cache: Optional[List[Dict[str, str]]] = None
        print(self.download_dir)
    # -------- HTTP helpers --------
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._tenant_token}",
        }

    def _get_with_retry(
        self,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Union[str, int]]] = None,
        timeout: int = 20,
        max_retries: int = 5,
        sleep_base: float = 1.0,
        expect_json: bool = True,
    ) -> requests.Response:
        """
        Basic retry with exponential backoff for Feishu rate limit (code 99991400).
        """
        attempt = 0
        while True:
            resp = self.session.get(url, headers=headers, params=params, timeout=timeout)
            # Try to detect rate-limit response payload
            is_rate_limited = False
            if expect_json:
                try:
                    payload = resp.json()
                    if payload.get("code") == 99991400:
                        is_rate_limited = True
                except Exception:
                    pass
            else:
                # non-JSON download may still be 400 with JSON body
                try:
                    payload = resp.json()
                    if payload.get("code") == 99991400:
                        is_rate_limited = True
                except Exception:
                    pass

            if not is_rate_limited or attempt >= max_retries:
                return resp

            # backoff and retry
            delay = sleep_base * (2**attempt)
            time.sleep(delay)
            attempt += 1

    def _ensure_token(self) -> None:
        if self._tenant_token:
            return
        resp = self.session.post(
            f"{BASE_URL}/auth/v3/tenant_access_token/internal/",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"get tenant_access_token failed: {data}")
        self._tenant_token = data["tenant_access_token"]

    # -------- records / attachments --------
    def _resolve_app_token_if_needed(self) -> str:
        """
        When FEISHU_APP_TOKEN is a wiki token (from feishu.cn/wiki/xxx),
        use knowledge API to resolve it to the underlying bitable app_token.
        """
        if self._resolved_app_token:
            return self._resolved_app_token
        # Already a bitable token
        if self.app_token.startswith("bascn"):
            self._resolved_app_token = self.app_token
            return self._resolved_app_token

        self._ensure_token()
        url = f"{BASE_URL}/wiki/v2/spaces/get_node"
        resp = self._get_with_retry(
            url,
            headers=self._headers(),
            params={"token": self.app_token},
            timeout=10,
        )
        if not resp.ok:
            raise RuntimeError(
                f"resolve wiki token failed: HTTP {resp.status_code} {resp.reason}; body={resp.text}"
            )
        payload = resp.json()
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        node = data.get("node", {}) if isinstance(data, dict) else {}
        obj_type = node.get("obj_type")
        obj_token = node.get("obj_token")
        if obj_type not in ("bitable", 4) or not obj_token:
            raise RuntimeError(f"resolve wiki token failed: unexpected node type: {payload}")
        self._resolved_app_token = obj_token
        return self._resolved_app_token

    def _list_records(self) -> List[Dict]:
        self._ensure_token()
        app_token = self._resolve_app_token_if_needed()
        records: List[Dict] = []
        page_token: Optional[str] = None
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{self.table_id}/records"
        while True:
            params: Dict[str, Union[str, int]] = {"page_size": 50}
            if self.view_id:
                params["view_id"] = self.view_id
            if page_token:
                params["page_token"] = page_token
            resp = self._get_with_retry(
                url, headers=self._headers(), params=params, timeout=20
            )
            if not resp.ok:
                raise RuntimeError(
                    f"list records failed: HTTP {resp.status_code} {resp.reason}; body={resp.text}"
                )
            payload = resp.json()
            if payload.get("code") != 0:
                raise RuntimeError(f"list records failed: {payload}")
            data = payload.get("data", {})
            records.extend(data.get("items", []))
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")
        return records

    def _iter_3mf_attachments(self, records: Iterable[Dict]) -> Iterable[Dict]:
        for rec in records:
            fields = rec.get("fields", {}) or {}
            attachments = fields.get(self.file_field, []) or []
            version = self._extract_version(fields)
            title = self._extract_title(fields)
            for idx, att in enumerate(attachments):
                name = att.get("name") or att.get("file_name") or ""
                file_token = att.get("file_token") or att.get("token")
                tmp_url = att.get("tmp_url") or att.get("url")
                if not name.lower().endswith(".3mf"):
                    continue
                if not file_token:
                    continue
                remote_ts = self._normalize_ts(
                    att.get("timestamp")
                    or att.get("mtime")
                    or att.get("modified_time")
                    or att.get("update_time")
                    or att.get("modified_at")
                    or att.get("created_at")
                )
                yield {
                    "record_id": rec.get("record_id") or rec.get("id"),
                    "name": name,
                    "file_token": file_token,
                    "tmp_url": tmp_url,
                    "index": idx,
                    "remote_ts": remote_ts,
                    "version": version,
                    "title": title,
                }

    def _download_one(self, attachment: Dict) -> Path:
        self._ensure_token()
        self.download_dir.mkdir(parents=True, exist_ok=True)
        safe_name = attachment["name"]
        target = self.download_dir / safe_name
        # If manifest already has a valid local file, skip download
        existing_path = self._find_existing_local(safe_name)
        print(f"existing_path: {existing_path}")
        if existing_path:
            target = Path(existing_path)
            self._record_download(
                name=attachment["name"],
                title=attachment.get("title"),
                version=attachment.get("version"),
                path=str(target),
            )
            return target
        # Deduplicate filename if same name but different file_token
        if target.exists() and str(target) != str(attachment.get("existing_path", "")):
            stem = target.stem
            suffix = target.suffix
            idx = 1
            while target.exists():
                target = self.download_dir / f"{stem}_{idx}{suffix}"
                idx += 1

        remote_ts = attachment.get("remote_ts")
        if remote_ts is not None and target.exists():
            local_ts = target.stat().st_mtime
            # Skip download when local file is same/newer than remote timestamp
            if local_ts >= remote_ts:
                self._record_download(
                    name=attachment["name"],
                    title=attachment.get("title"),
                    version=attachment.get("version"),
                    path=str(target),
                )
                return target

        # Prefer tmp_url if provided, otherwise fall back to drive download API.
        # Step 1: request download handle (may return json with tmp_download_url)
        if attachment.get("tmp_url"):
            resp = self._get_with_retry(
                attachment["tmp_url"],
                headers=self._headers(),
                timeout=120,
                expect_json=False,
                max_retries=5,
                sleep_base=1.0,
            )
        else:
            download_url = f"{BASE_URL}/drive/v1/files/{attachment['file_token']}/download"
            resp = self._get_with_retry(
                download_url,
                headers=self._headers(),
                timeout=120,
                expect_json=False,
                max_retries=5,
                sleep_base=1.0,
            )

        # Step 2: if response is JSON with tmp_download_url, fetch the actual file
        actual_resp = resp
        try:
            payload = resp.json()
        except Exception:
            payload = None

        if payload and isinstance(payload, dict) and payload.get("code") == 0:
            urls = payload.get("data", {}).get("tmp_download_urls") or []
            tmp_dl = None
            if urls and isinstance(urls, list):
                first = urls[0] or {}
                tmp_dl = first.get("tmp_download_url") or first.get("url")
            if not tmp_dl:
                raise RuntimeError(f"download failed: no tmp_download_url in response {payload}")
            actual_resp = self._get_with_retry(
                tmp_dl,
                headers=self._headers(),
                timeout=120,
                expect_json=False,
                max_retries=5,
                sleep_base=1.0,
            )

        if not actual_resp.ok:
            raise RuntimeError(
                f"download failed: HTTP {actual_resp.status_code} {actual_resp.reason}; body={actual_resp.text}"
            )

        with open(target, "wb") as f:
            f.write(actual_resp.content)
        if remote_ts is not None:
            # set mtime to remote timestamp to keep consistency
            os.utime(target, times=(remote_ts, remote_ts))
        self._record_download(
            name=attachment["name"],
            title=attachment.get("title"),
            version=attachment.get("version"),
            path=str(target),
        )
        return target

    @staticmethod
    def _normalize_ts(ts: Union[str, int, float, None]) -> Optional[float]:
        """
        Normalize timestamp to seconds (float). Accepts:
        - milliseconds (int/float > 1e12)
        - seconds (int/float)
        - ISO8601 string
        """
        if ts is None:
            return None
        if isinstance(ts, (int, float)):
            val = float(ts)
            if val > 1e12:
                return val / 1000.0
            return val
        if isinstance(ts, str):
            try:
                num = float(ts)
                if num > 1e12:
                    return num / 1000.0
                return num
            except ValueError:
                pass
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return dt.timestamp()
            except ValueError:
                return None
        return None

    def _record_download(self, name: str, title: Optional[str], version: Optional[Union[str, int]], path: str) -> None:
        """
        Append/update manifest of downloaded files:
        [
            { "name": "...", "title": "...", "software_version": "...", "path": "..." },
            ...
        ]
        """
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "name": name,
            "title": title or "",
            "software_version": str(version) if version is not None else "",
            "path": path,
        }
        manifest = self._load_manifest()

        updated = False
        for idx, item in enumerate(manifest):
            if item.get("name") == name:
                manifest[idx] = entry
                updated = True
                break
        if not updated:
            manifest.append(entry)

        tmp = self.manifest_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.manifest_path)
        self._manifest_cache = manifest

    @staticmethod
    def _extract_version(fields: Dict) -> Optional[str]:
        """
        Try to extract software version from table fields by common keys.
        """
        version_keys = ["软件版本", "版本", "version", "软件Version", "software_version"]
        for key in version_keys:
            if key in fields:
                val = fields.get(key)
                if val is None:
                    continue
                if isinstance(val, (str, int, float)):
                    return str(val)
                # handle single-element list
                if isinstance(val, list) and val:
                    v0 = val[0]
                    if isinstance(v0, (str, int, float)):
                        return str(v0)
        return None

    @staticmethod
    def _extract_title(fields: Dict) -> Optional[str]:
        """
        Extract a display title from common field names.
        """
        title_keys = ["名称", "标题", "name", "title", "文件名称"]
        for key in title_keys:
            if key in fields:
                val = fields.get(key)
                if val is None:
                    continue
                if isinstance(val, (str, int, float)):
                    return str(val)
                if isinstance(val, list) and val:
                    v0 = val[0]
                    if isinstance(v0, (str, int, float)):
                        return str(v0)
        return None

    def _load_manifest(self) -> List[Dict[str, str]]:
        if self._manifest_cache is not None:
            return list(self._manifest_cache)
        manifest: List[Dict[str, str]] = []
        if self.manifest_path.exists():
            try:
                manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                if not isinstance(manifest, list):
                    manifest = []
            except Exception:
                manifest = []
        self._manifest_cache = manifest
        return list(manifest)

    def _find_existing_local(self, name: str) -> Optional[str]:
        manifest = self._load_manifest()
        for item in manifest:
            if item.get("name") == name:
                path = item.get("path")
                if path and Path(path).exists():
                    return path
        return None

    def download_all(self) -> List[Dict]:
        """
        Download all 3MF attachments and return a list of dicts:
        [{ 'record_id': str, 'name': str, 'path': Path }]
        """
        records = self._list_records()
        results: List[Dict] = []
        for att in self._iter_3mf_attachments(records):
            path = self._download_one(att)
            print(f"Downloading attachment: {att['name']}")
            results.append(
                {
                    "record_id": att.get("record_id"),
                    "name": att["name"],
                    "path": path,
                }
            )
        return results
