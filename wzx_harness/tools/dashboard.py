#!/usr/bin/env python3
"""wzx_harness 本地可视化操作台（纯标准库，零依赖）。

功能：
  - 基线表格（baseline.csv，含逐段耗时展开）
  - 最近一次运行报告（artifacts/run_report.csv）
  - 阶段对比表（artifacts/stage_comparison.md）
  - Linux 门禁各套件日志摘要
  - 运行按钮：Linux 门禁 / 模型回归（双引擎）/ 基线更新，实时输出

用法： python3 dashboard.py [--port 8765]
浏览器打开 http://127.0.0.1:8765
"""

import csv
import json
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HARNESS = Path(__file__).resolve().parent.parent  # wzx_harness/
LOGDIR = Path("/tmp/owzx_linux_gate")
REPO = HARNESS.parent.parent / "3DPrinter_Qt6"

GATE_SUITES = ["CliTests", "E2EWorkflowTests", "ViewModelSmokeTests",
               "PrepareSceneDataTests", "ObjectPickingTests", "NavigatorCubeTests",
               "CameraParityTests", "ViewportContextMenuTests", "QmlUiAuditTests",
               "PartPlateTests", "AppToolTests", "PreviewParserTests",
               "GizmoGeometryTests", "QmlSmokeTests"]

RUNS = {}  # name -> {"proc": Popen, "log": Path}
RUN_CMDS = {
    "gate": {
        "title": "Linux 门禁（14 套件）",
        "cmd": ["bash", str(REPO / "scripts" / "verify_linux.sh")],
    },
    "regression": {
        "title": "模型回归（30 模型 × 双引擎，回退即红）",
        "cmd": [str(HARNESS / ".venv" / "bin" / "pytest"), "case/test_slice.py",
                "--slicer-exe", str(REPO / "build" / "owzx-cli"),
                "--orca-exe", str(REPO.parent / "OrcaSlicer" / "build" / "src" / "orca-slicer"),
                "--models-dir", "/home/admins/公共/CP/wzx_models",
                "--case-regex", "^(?!heavy/)", "--case-timeout", "1800", "-v"],
        "cwd": str(HARNESS),
    },
    "baseline": {
        "title": "基线更新（--update-baseline，重录）",
        "cmd": [str(HARNESS / ".venv" / "bin" / "pytest"), "case/test_slice.py",
                "--slicer-exe", str(REPO / "build" / "owzx-cli"),
                "--orca-exe", str(REPO.parent / "OrcaSlicer" / "build" / "src" / "orca-slicer"),
                "--models-dir", "/home/admins/公共/CP/wzx_models",
                "--case-regex", "^(?!heavy/)", "--case-timeout", "1800",
                "--update-baseline", "-v"],
        "cwd": str(HARNESS),
    },
}


def read_csv(path):
    path = Path(path)
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body if isinstance(body, bytes) else body.encode("utf-8"))

    def do_GET(self):
        route = urlparse(self.path).path
        if route in ("/", "/index.html"):
            return self._send(200, PAGE)
        if route == "/api/baseline":
            rows = read_csv(HARNESS / "data" / "baseline.csv")
            for r in rows:
                try:
                    r["_stages"] = json.loads(r.get("stages_json") or "{}")
                except Exception:
                    r["_stages"] = {}
            return self._send(200, json.dumps(rows, ensure_ascii=False), "application/json")
        if route == "/api/report":
            return self._send(200, json.dumps(
                read_csv(HARNESS / "artifacts" / "run_report.csv"), ensure_ascii=False),
                "application/json")
        if route == "/api/stages":
            p = HARNESS / "artifacts" / "stage_comparison.md"
            return self._send(200, p.read_text(encoding="utf-8") if p.is_file() else "(尚未生成)",
                              "text/plain; charset=utf-8")
        if route == "/api/gate":
            data = []
            for s in GATE_SUITES:
                p = LOGDIR / f"{s}.log"
                totals, first_fail = "", ""
                if p.is_file():
                    lines = p.read_text(errors="replace").splitlines()
                    for line in reversed(lines):
                        if "Totals:" in line:
                            totals = line.strip()
                            break
                    for line in lines:
                        if line.startswith("FAIL"):
                            first_fail = line[:120]
                            break
                data.append({"suite": s, "totals": totals, "fail": first_fail,
                             "exists": p.is_file()})
            return self._send(200, json.dumps(data, ensure_ascii=False), "application/json")
        if route == "/api/runs":
            out = {name: {"title": cfg["title"],
                          "running": RUNS.get(name, {}).get("proc") is not None and
                                      RUNS[name]["proc"].poll() is None,
                          "log": str(RUNS[name]["log"]) if name in RUNS else ""}
                   for name, cfg in RUN_CMDS.items()}
            return self._send(200, json.dumps(out, ensure_ascii=False), "application/json")
        if route.startswith("/api/runlog/"):
            name = route.rsplit("/", 1)[-1]
            if name in RUNS and RUNS[name]["log"].is_file():
                text = RUNS[name]["log"].read_text(errors="replace")[-20000:]
                rc = RUNS[name]["proc"].poll() if RUNS[name].get("proc") else None
                return self._send(200, json.dumps({"rc": rc, "text": text},
                                                  ensure_ascii=False), "application/json")
            return self._send(200, json.dumps({"rc": None, "text": "(无)"}, ensure_ascii=False),
                              "application/json")
        return self._send(404, "not found", "text/plain")

    def do_POST(self):
        if urlparse(self.path).path != "/api/run":
            return self._send(404, "not found", "text/plain")
        length = int(self.headers.get("Content-Length") or 0)
        name = self.rfile.read(length).decode().strip()
        if name not in RUN_CMDS:
            return self._send(400, "unknown run", "text/plain")
        cur = RUNS.get(name)
        if cur and cur["proc"].poll() is None:
            return self._send(409, "已在运行", "text/plain")
        cfg = RUN_CMDS[name]
        log = HARNESS / "artifacts" / f"run_{name}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        fh = log.open("w")
        proc = subprocess.Popen(cfg["cmd"], stdout=fh, stderr=subprocess.STDOUT,
                                cwd=cfg.get("cwd"))
        RUNS[name] = {"proc": proc, "log": log}
        return self._send(200, f"已启动: {cfg['title']}\n日志: {log}", "text/plain")


PAGE = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>wzx_harness 操作台</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#111;color:#ddd}
nav{display:flex;gap:4px;padding:10px;background:#1b1b1b;flex-wrap:wrap}
nav button{padding:8px 14px;border:0;border-radius:6px;background:#333;color:#ddd;cursor:pointer}
nav button.on{background:#0a7;color:#fff}
main{padding:14px;overflow:auto}
table{border-collapse:collapse;width:100%;font-size:13px}
td,th{border:1px solid #333;padding:4px 8px;text-align:left}
th{background:#222;position:sticky;top:0}
tr:hover td{background:#1e2a1e}
.ok{color:#5c5}.bad{color:#f66}
pre{background:#181818;padding:10px;border-radius:6px;overflow:auto;max-height:70vh;font-size:12px}
.btn{background:#0a7;color:#fff;border:0;padding:10px 18px;border-radius:6px;cursor:pointer;margin:4px}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;background:#333;margin-right:6px}
#runout{background:#000;color:#9f9;font-family:monospace;font-size:12px;
 max-height:55vh;overflow:auto;padding:10px;white-space:pre-wrap}
</style><body>
<nav id="tabs"></nav><main id="main">加载中…</main>
<script>
const TABS = ["基线","运行报告","阶段对比","Linux 门禁","运行"];
async function jget(u){ const r = await fetch(u); return r.text(); }
function esc(s){ return (s??"").replace(/&/g,"&amp;").replace(/</g,"&lt;"); }

async function showBaseline(){
  const rows = JSON.parse(await jget("/api/baseline"));
  let h = "<h3>基线（"+rows.length+" 行 · 双引擎 · 含逐段耗时）</h3><table><tr><th>模型</th><th>平台</th><th>版本</th><th>总耗时(ms)</th><th>层数</th><th>切片</th><th>导出</th><th>Orca(ms)</th><th>比值</th><th>逐段耗时</th></tr>";
  for (const r of rows){
    const stages = Object.entries(r._stages||{}).map(([k,v])=>k+":"+Math.round(v)).join(" | ");
    h += `<tr><td>${esc(r.model)}</td><td>${r.os}</td><td>${esc(r.version)}</td>
      <td>${Math.round(r.total_ms)}</td><td>${r.gcode_layers}</td>
      <td class="${r.slice_ok==='True'?'ok':'bad'}">${r.slice_ok}</td>
      <td class="${r.export_ok==='True'?'ok':'bad'}">${r.export_ok}</td>
      <td>${Math.round(r.orca_ms||0)||'—'}</td><td>${esc(r.orca_ratio||'—')}</td>
      <td style="font-size:11px;color:#8ab">${esc(stages)}</td></tr>`;
  }
  document.getElementById("main").innerHTML = h+"</table>";
}
async function showReport(){
  const rows = JSON.parse(await jget("/api/report"));
  let h = "<h3>最近运行报告（"+rows.length+" 行）</h3><table><tr><th>模型</th><th>总耗时</th><th>层数</th><th>切片</th><th>导出</th><th>崩溃</th><th>Orca(ms)</th><th>比值</th><th>错误</th></tr>";
  for (const r of rows){
    h += `<tr><td>${esc(r.model)}</td><td>${Math.round(r.total_ms)}</td><td>${r.gcode_layers}</td>
      <td class="${r.slice_ok==='True'?'ok':'bad'}">${r.slice_ok}</td>
      <td class="${r.export_ok==='True'?'ok':'bad'}">${r.export_ok}</td>
      <td class="${r.crashed==='True'?'bad':'ok'}">${r.crashed}</td>
      <td>${Math.round(r.orca_ms||0)||'—'}</td><td>${esc(r.orca_ratio||'—')}</td>
      <td style="color:#f96">${esc(r.error).slice(0,120)}</td></tr>`;
  }
  document.getElementById("main").innerHTML = h+"</table>";
}
async function showStages(){
  document.getElementById("main").innerHTML = "<h3>阶段对比（原样）</h3><pre>"+esc(await jget("/api/stages"))+"</pre>";
}
async function showGate(){
  const data = JSON.parse(await jget("/api/gate"));
  let h = "<h3>Linux 门禁（14 套件）</h3><table><tr><th>套件</th><th>状态</th><th>Totals</th><th>首个失败</th></tr>";
  for (const d of data){
    const okRun = d.totals.includes("0 failed") && d.exists;
    h += `<tr><td>${d.suite}</td><td class="${d.exists?(okRun?'ok':'bad'):'bad'}">${d.exists?(okRun?'PASS':'FAIL'):'无日志'}</td>
      <td style="font-size:11px">${esc(d.totals)}</td><td style="color:#f96;font-size:11px">${esc(d.fail)}</td></tr>`;
  }
  document.getElementById("main").innerHTML = h+"</table><p style='color:#888'>日志目录: /tmp/owzx_linux_gate（「运行」页重新生成）</p>";
}
let pollTimer = null;
async function showRuns(){
  const runs = JSON.parse(await jget("/api/runs"));
  let h = "<h3>运行</h3>";
  for (const [name,r] of Object.entries(runs)){
    h += `<p><span class="badge">${r.running?"🟢 运行中":"⚪ 空闲"}</span> <b>${esc(r.title)}</b>
      <button class="btn" onclick="startRun('${name}')">启动</button>
      ${r.log?`<button class="btn" style="background:#357" onclick="tailRun('${name}')">看日志</button>`:""}</p>`;
  }
  h += "<div id='runout'>（点「看日志」或启动后自动刷新）</div>";
  document.getElementById("main").innerHTML = h;
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async ()=>{
    const out = document.getElementById("runout");
    if (!out) { clearInterval(pollTimer); return; }
    for (const name of Object.keys(runs)){
      if (window._tail === name){
        const d = JSON.parse(await jget("/api/runlog/"+name));
        out.textContent = d.text + (d.rc!==null ? "[结束 rc="+d.rc+"]" : "[运行中…]");
        out.scrollTop = out.scrollHeight;
      }
    }
  }, 2000);
}
async function startRun(name){
  await fetch("/api/run", {method:"POST", body:name});
  window._tail = name; showRuns();
}
async function tailRun(name){ window._tail = name;
  const d = JSON.parse(await jget("/api/runlog/"+name));
  document.getElementById("runout").textContent = d.text; }
function tab(name){
  document.querySelectorAll("#tabs button").forEach(b=>b.classList.toggle("on",b.textContent===name));
  if(name==="基线") showBaseline();
  if(name==="运行报告") showReport();
  if(name==="阶段对比") showStages();
  if(name==="Linux 门禁") showGate();
  if(name==="运行") showRuns();
}
const nav = document.getElementById("tabs");
for (const t of TABS){ const b=document.createElement("button"); b.textContent=t;
  b.onclick=()=>tab(t); nav.appendChild(b); }
tab("基线");
</script>"""


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"操作台: http://127.0.0.1:{args.port}  (Ctrl-C 退出)")
    server.serve_forever()


if __name__ == "__main__":
    main()
