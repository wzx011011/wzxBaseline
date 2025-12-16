"""
C3DBaseline 测试运行器 - 一键启动脚本
自动生成测试列表、启动服务器、打开浏览器
"""
import subprocess
import time
import webbrowser
import sys
import os
import argparse
from pathlib import Path
import socket

def check_port_available(port=8888):
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result != 0  # 0表示端口被占用
    except:
        return True

def kill_existing_server(port=8888):
    """尝试终止占用端口的进程"""
    try:
        if sys.platform == 'win32':
            # Windows系统
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'LISTENING' in line:
                        parts = line.split()
                        pid = parts[-1]
                        print(f"⚠️  发现端口 {port} 被进程 {pid} 占用，正在终止...")
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                        time.sleep(1)
                        return True
        return False
    except Exception as e:
        print(f"⚠️  清理端口时出错: {e}")
        return False

def generate_test_data(verbose=False):
    """生成测试用例数据"""
    print("=" * 60)
    print("📋 步骤 1/3: 收集测试用例")
    print("=" * 60)
    
    web_dir = Path(__file__).parent
    script = web_dir / "generate_test_selector.py"
    
    # 检查是否已有数据
    json_file = web_dir / "tests_data.json"
    if json_file.exists():
        file_age = time.time() - json_file.stat().st_mtime
        if verbose:
            print(f"💡 发现现有数据文件（{int(file_age/60)} 分钟前生成）")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=web_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'  # 忽略编码错误
        )
        
        elapsed = time.time() - start_time
        
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"❌ 生成测试数据失败: {result.stderr}")
            return False
        
        if verbose:
            print(f"⏱️  收集耗时: {elapsed:.2f} 秒")
        
        return True
    except Exception as e:
        print(f"❌ 执行生成脚本失败: {e}")
        return False

def start_server(port=8888, verbose=False):
    """启动测试服务器"""
    print("\n" + "=" * 60)
    print(f"🚀 步骤 2/3: 启动测试服务器 (端口 {port})")
    print("=" * 60)
    
    # 检查端口
    if not check_port_available(port):
        print(f"⚠️  端口 {port} 已被占用")
        killed = kill_existing_server(port)
        
        if not killed:
            print(f"❌ 无法清理端口 {port}，请手动关闭占用该端口的程序")
            user_input = input("是否尝试使用其他端口？(y/n): ").lower()
            if user_input == 'y':
                port = int(input("请输入新端口号: "))
                return start_server(port, verbose)
            return None
    
    web_dir = Path(__file__).parent
    server_script = web_dir / "test_runner_server.py"
    
    try:
        # 在后台启动服务器
        if sys.platform == 'win32':
            # Windows: 使用 CREATE_NEW_CONSOLE 标志在新窗口启动
            process = subprocess.Popen(
                [sys.executable, str(server_script), '--port', str(port)],
                cwd=web_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Linux/Mac
            process = subprocess.Popen(
                [sys.executable, str(server_script), '--port', str(port)],
                cwd=web_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        print(f"✅ 服务器进程已启动 (PID: {process.pid})")
        
        # 等待服务器启动
        print("⏳ 等待服务器就绪...", end="", flush=True)
        max_wait = 10  # 最多等待10秒
        
        for i in range(max_wait):
            time.sleep(1)
            print(".", end="", flush=True)
            
            if not check_port_available(port):
                print(" 完成!")
                if verbose:
                    print(f"💡 服务器已在 http://localhost:{port} 就绪")
                return process, port
        
        print("\n❌ 服务器启动超时")
        print("💡 提示: 检查是否有防火墙阻止，或查看服务器窗口的错误信息")
        process.terminate()
        return None, port
        
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return None, port

def open_browser(url="http://localhost:8888", auto_open=True):
    """在浏览器中打开测试选择器"""
    print("\n" + "=" * 60)
    print("🌐 步骤 3/3: 打开浏览器")
    print("=" * 60)
    
    if not auto_open:
        print(f"💡 自动打开浏览器已禁用")
        print(f"   请手动访问: {url}")
        return True
    
    try:
        webbrowser.open(url)
        print(f"✅ 浏览器已打开: {url}")
        return True
    except Exception as e:
        print(f"❌ 打开浏览器失败: {e}")
        print(f"💡 请手动在浏览器中访问: {url}")
        return False

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='C3DBaseline 测试运行器 - 一键启动脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python start_test.py                    # 默认启动（端口8888，自动打开浏览器）
  python start_test.py --port 9000        # 指定端口
  python start_test.py --no-browser       # 不自动打开浏览器
  python start_test.py --skip-generate    # 跳过测试收集，使用现有数据
  python start_test.py -v                 # 详细模式
        """
    )
    
    parser.add_argument('--port', type=int, default=8888,
                        help='服务器端口号 (默认: 8888)')
    parser.add_argument('--no-browser', action='store_true',
                        help='不自动打开浏览器')
    parser.add_argument('--skip-generate', action='store_true',
                        help='跳过测试数据生成，使用现有 tests_data.json')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='显示详细信息')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    print("\n" + "🧪" * 30)
    print("    C3DBaseline 测试运行器 - 一键启动")
    print("🧪" * 30 + "\n")
    
    if args.verbose:
        print(f"📝 配置:")
        print(f"   端口: {args.port}")
        print(f"   自动打开浏览器: {not args.no_browser}")
        print(f"   跳过测试收集: {args.skip_generate}")
        print()
    
    # 步骤1: 生成测试数据
    if args.skip_generate:
        print("=" * 60)
        print("📋 步骤 1/3: 跳过测试收集（使用现有数据）")
        print("=" * 60)
        
        json_file = Path(__file__).parent / "tests_data.json"
        if not json_file.exists():
            print("❌ 未找到 tests_data.json，需要先生成数据")
            print("💡 请移除 --skip-generate 参数重新运行")
            input("按 Enter 键退出...")
            return 1
        print(f"✅ 使用现有数据: {json_file}")
    else:
        if not generate_test_data(args.verbose):
            print("\n❌ 启动失败：无法生成测试数据")
            user_input = input("是否重试？(y/n): ").lower()
            if user_input == 'y':
                if not generate_test_data(args.verbose):
                    print("❌ 重试失败")
                    input("按 Enter 键退出...")
                    return 1
            else:
                return 1
    
    # 步骤2: 启动服务器
    result = start_server(args.port, args.verbose)
    if result is None or result[0] is None:
        print("\n❌ 启动失败：无法启动服务器")
        input("按 Enter 键退出...")
        return 1
    
    server_process, actual_port = result
    url = f"http://localhost:{actual_port}"
    
    # 步骤3: 打开浏览器
    open_browser(url, not args.no_browser)
    
    # 启动完成
    print("\n" + "=" * 60)
    print("✅ 所有服务已就绪！")
    print("=" * 60)
    print("\n📌 使用说明：")
    print("   • 在浏览器中选择要运行的测试用例")
    print("   • 点击 '▶️ 运行选中的测试' 按钮")
    print("   • 测试输出会实时显示在右侧面板")
    print(f"\n🌐 访问地址: {url}")
    print("\n⚠️  注意事项：")
    print("   • 服务器正在后台运行（独立窗口）")
    print("   • 关闭该窗口即可停止服务器")
    print("   • 也可以在浏览器中使用停止按钮")
    print("\n" + "=" * 60)
    print("🎉 祝测试顺利！")
    print("=" * 60 + "\n")
    
    # 保持脚本运行，显示提示信息
    try:
        print("💡 提示：关闭此窗口将退出启动程序（服务器继续运行）")
        print("        按 Ctrl+C 可以立即退出\n")
        input("按 Enter 键退出启动程序...")
    except KeyboardInterrupt:
        print("\n\n👋 再见！")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出程序")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 键退出...")
        sys.exit(1)
