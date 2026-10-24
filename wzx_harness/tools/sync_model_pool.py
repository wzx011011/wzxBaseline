#!/usr/bin/env python3
"""Sync the C3DBaseline model pool (http://172.20.180.14/shared/test_3mf/ty/)
into a local directory, preserving the category tree.

Usage:
    sync_model_pool.py --dest /path/to/wzx_models [--only 效率,卡在25%] [--max-mb 30]

Resumable: skips files that already exist with the right size.
>max-mb files go into <dest>/heavy/ (big-RAM machines only).
Model files are data, not code — keep <dest> outside any git repo.
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, unquote, urlsplit, urlunsplit, quote

BASE = "http://172.20.180.14/shared/test_3mf/ty/"


def crawl(url, seen, files):
    if url in seen:
        return
    seen.add(url)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8", "replace")
    for href in re.findall(r'href="([^"]+)"', body):
        if href.startswith(("?", "/")):
            continue
        full = urljoin(url, href)
        if href.endswith("/"):
            crawl(full, seen, files)
        elif href.lower().endswith((".3mf", ".stl")):
            files.append((full, unquote(full).replace(unquote(BASE), "")))


def fixed_url(u):
    sp = urlsplit(u)
    # safe='/%' keeps existing %XX escapes intact (listings pre-encode Chinese
    # dirs) while still encoding spaces and raw unicode in file names.
    return urlunsplit((sp.scheme, sp.netloc, quote(sp.path, safe="/%"), sp.query, sp.fragment))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--only", default="", help="comma-separated category prefixes to keep")
    ap.add_argument("--max-mb", type=int, default=30)
    args = ap.parse_args()

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    keep = [k for k in args.only.split(",") if k]

    seen, files = set(), []
    print("crawling index ...")
    crawl(BASE, seen, files)
    print(f"pool: {len(files)} models")

    if keep:
        files = [(u, rel) for u, rel in files if any(k in unquote(rel) for k in keep)]
        print(f"filtered to {len(files)} by {keep}")

    ok_n = skip_n = heavy_n = fail_n = 0
    for url, rel in sorted(files, key=lambda x: x[1]):
        target = dest / "heavy" / unquote(rel) if False else dest / unquote(rel)
        # size probe happens on download; heavy routing after first byte is
        # complex — instead pre-route via HEAD with Range (cheap).
        try:
            req = urllib.request.Request(
                fixed_url(url), headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-0"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                cr = r.headers.get("Content-Range") or ""
                size = int(cr.split("/")[-1]) if cr else 0
        except Exception as exc:
            print(f"SKIP (unreachable): {rel[:70]} {exc}")
            fail_n += 1
            continue
        if size and size > args.max_mb * 1000_000:
            target = dest / "heavy" / unquote(rel)
            heavy_n += 1
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file() and target.stat().st_size == size:
            skip_n += 1
            continue
        tmp = target.with_suffix(target.suffix + ".part")
        try:
            urllib.request.urlretrieve(fixed_url(url), tmp)
            tmp.rename(target)
            ok_n += 1
            print(f"ok: {unquote(rel)[:70]} ({size/1e6:.1f}MB)")
        except Exception as exc:
            fail_n += 1
            print(f"FAIL: {rel[:70]} {exc}")
            tmp.unlink(missing_ok=True)
        time.sleep(0.05)

    print(f"\ndone: new={ok_n} skipped={skip_n} heavy={heavy_n} fail={fail_n}")


if __name__ == "__main__":
    main()
