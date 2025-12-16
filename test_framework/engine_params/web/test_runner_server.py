"""
测试运行服务器 - 提供Web界面运行pytest并实时显示输出
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import threading
import queue
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

class TestRunnerHandler(BaseHTTPRequestHandler):
    # 用于存储测试进程和输出队列
    test_process = None
    output_queue = queue.Queue()
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # 返回HTML页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_file = Path(__file__).parent / 'test_selector_hierarchical.html'
            with open(html_file, 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
        
        elif parsed_path.path == '/status':
            # 返回测试运行状态
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            is_running = TestRunnerHandler.test_process is not None and TestRunnerHandler.test_process.poll() is None
            self.wfile.write(json.dumps({'running': is_running}).encode('utf-8'))
        
        elif parsed_path.path == '/output':
            # 流式返回测试输出
            self.send_response(200)
            self.send_header('Content-type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                while True:
                    try:
                        # 从队列获取输出，超时1秒
                        line = TestRunnerHandler.output_queue.get(timeout=1)
                        if line is None:  # 结束信号
                            break
                        # 发送SSE格式数据
                        self.wfile.write(f"data: {json.dumps({'line': line})}\n\n".encode('utf-8'))
                        self.wfile.flush()
                    except queue.Empty:
                        # 检查进程是否还在运行
                        if TestRunnerHandler.test_process and TestRunnerHandler.test_process.poll() is not None:
                            break
                        # 发送心跳
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == '/run':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            deselected = data.get('deselected', [])
            
            # 设置环境变量
            env = os.environ.copy()
            env['CREALITY_PRINTER_PATH'] = r"C:\Program Files\Creality\Creality Print 7.0 Beta\CrealityPrint.exe"
            env['PYTHONPATH'] = str(Path(__file__).parent.parent.parent)
            
            # 清空输出队列
            while not TestRunnerHandler.output_queue.empty():
                try:
                    TestRunnerHandler.output_queue.get_nowait()
                except queue.Empty:
                    break
            
            # 启动测试进程
            def run_tests():
                # 如果排除的测试太多，使用临时配置文件
                if len(deselected) > 50:
                    import tempfile
                    # 创建临时的pytest.ini配置
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                        deselect_file = f.name
                        for test_path in deselected:
                            f.write(f"engine_params/case/params/{test_path}\n")
                    
                    try:
                        # 使用Python脚本来调用pytest，避免命令行长度限制
                        script = f'''
import sys
import pytest

# 读取排除列表
with open(r"{deselect_file}", "r", encoding="utf-8") as f:
    deselected = [line.strip() for line in f if line.strip()]

# 构建参数
args = ["engine_params/case/params/", "-v", "--tb=line"]
for test in deselected:
    args.extend(["--deselect", test])

# 运行pytest
sys.exit(pytest.main(args))
'''
                        script_file = Path(__file__).parent.parent.parent / '_temp_run_tests.py'
                        with open(script_file, 'w', encoding='utf-8') as f:
                            f.write(script)
                        
                        TestRunnerHandler.test_process = subprocess.Popen(
                            ['python', str(script_file)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            cwd=Path(__file__).parent.parent.parent,
                            env=env
                        )
                    finally:
                        import time
                        time.sleep(0.5)  # 等待文件被读取
                        try:
                            os.unlink(deselect_file)
                        except:
                            pass
                else:
                    # 排除的测试较少，直接使用命令行
                    cmd = ['pytest', 'engine_params/case/params/', '-v', '--tb=line']
                    for test_path in deselected:
                        cmd.extend(['--deselect', f'engine_params/case/params/{test_path}'])
                    
                    TestRunnerHandler.test_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        cwd=Path(__file__).parent.parent.parent,
                        env=env
                    )
                
                # 读取输出并放入队列
                for line in iter(TestRunnerHandler.test_process.stdout.readline, ''):
                    if line:
                        TestRunnerHandler.output_queue.put(line.rstrip())
                
                TestRunnerHandler.test_process.wait()
                TestRunnerHandler.output_queue.put(None)  # 结束信号
                
                # 清理临时脚本
                try:
                    script_file = Path(__file__).parent.parent.parent / '_temp_run_tests.py'
                    if script_file.exists():
                        os.unlink(script_file)
                except:
                    pass
            
            thread = threading.Thread(target=run_tests, daemon=True)
            thread.start()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'started'}).encode('utf-8'))
        
        elif self.path == '/stop':
            # 停止测试
            if TestRunnerHandler.test_process:
                TestRunnerHandler.test_process.terminate()
                try:
                    TestRunnerHandler.test_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    TestRunnerHandler.test_process.kill()
                TestRunnerHandler.test_process = None
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'stopped'}).encode('utf-8'))
        
        elif self.path == '/shutdown':
            # 关闭服务器
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'shutting down'}).encode('utf-8'))
            
            # 在新线程中关闭服务器
            def shutdown():
                import time
                time.sleep(0.5)
                self.server.shutdown()
            
            threading.Thread(target=shutdown, daemon=True).start()
    
    def log_message(self, format, *args):
        """自定义日志输出"""
        pass  # 静默HTTP请求日志

def run_server(port=8000):
    """启动Web服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, TestRunnerHandler)
    print(f"🌐 测试运行器服务已启动: http://localhost:{port}")
    print(f"📋 在浏览器中打开上述地址即可使用")
    print(f"按 Ctrl+C 停止服务器")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹ 正在停止服务器...")
        # 终止正在运行的测试进程
        if TestRunnerHandler.test_process:
            try:
                TestRunnerHandler.test_process.terminate()
                TestRunnerHandler.test_process.wait(timeout=3)
            except:
                try:
                    TestRunnerHandler.test_process.kill()
                except:
                    pass
        httpd.server_close()
        print("✅ 服务器已停止")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='C3DBaseline 测试运行器服务器')
    parser.add_argument('--port', type=int, default=8888, help='服务器端口号 (默认: 8888)')
    args = parser.parse_args()
    
    run_server(port=args.port)
