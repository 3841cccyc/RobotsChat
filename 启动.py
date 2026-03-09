#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import webbrowser
import signal
import atexit

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_banner():
    print(f"{Colors.CYAN}========================================{Colors.RESET}")
    print(f"{Colors.CYAN}   机器人对话系统 - 一键启动{Colors.RESET}")
    print(f"{Colors.CYAN}========================================{Colors.RESET}")
    print()

def check_env_var():
    api_key = os.environ.get("MINIMAX_API_KEY", "")
    if not api_key:
        print(f"{Colors.RED}   错误: 未设置 MINIMAX_API_KEY 环境变量{Colors.RESET}")
        print(f"{Colors.YELLOW}   请在系统环境变量中设置:{Colors.RESET}")
        print(f"   Windows: setx MINIMAX_API_KEY \"你的API密钥\"")
        print(f"   或在当前终端: $env:MINIMAX_API_KEY=\"你的API密钥\"")
        return False
    print(f"{Colors.GREEN}   MINIMAX_API_KEY 已设置 ✓{Colors.RESET}")
    return True

def start_backend():
    print(f"{Colors.YELLOW}[2/3] 启动后端服务...{Colors.RESET}")
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    venv_python = os.path.join(os.path.dirname(__file__), '.venv', 'Scripts', 'python.exe')

    if not os.path.exists(venv_python):
        venv_python = 'python'

    env = os.environ.copy()
    env["MINIMAX_API_KEY"] = os.environ.get("MINIMAX_API_KEY", "")

    proc = subprocess.Popen(
        [venv_python, '-m', 'app.main'],
        cwd=backend_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
        env=env
    )
    print(f"{Colors.GREEN}   后端已启动 (PID: {proc.pid}){Colors.RESET}")
    return proc

def start_frontend():
    print(f"{Colors.YELLOW}[3/3] 启动前端服务...{Colors.RESET}")
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    vite_exe = os.path.join(frontend_dir, 'node_modules', '.bin', 'vite.cmd')

    if not os.path.exists(vite_exe):
        vite_exe = os.path.join(frontend_dir, 'node_modules', '.bin', 'vite')

    if os.path.exists(vite_exe):
        proc = subprocess.Popen(
            [vite_exe],
            cwd=frontend_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
    else:
        proc = subprocess.Popen(
            ['npx', 'vite'],
            cwd=frontend_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
    print(f"{Colors.GREEN}   前端已启动 (PID: {proc.pid}){Colors.RESET}")
    return proc

def cleanup(processes):
    print(f"\n{Colors.YELLOW}正在停止服务...{Colors.RESET}")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            try:
                proc.kill()
            except:
                pass
    print(f"{Colors.GREEN}服务已停止{Colors.RESET}")

def main():
    processes = []
    print_banner()

    print(f"{Colors.YELLOW}[1/3] 检查环境变量...{Colors.RESET}")
    if not check_env_var():
        input(f"\n{Colors.YELLOW}按回车键退出...{Colors.RESET}")
        sys.exit(1)
    print()

    try:
        processes.append(start_backend())
        print()
        processes.append(start_frontend())
        print()

        print(f"{Colors.YELLOW}等待服务启动...{Colors.RESET}")
        time.sleep(5)

        print()
        print(f"{Colors.CYAN}========================================{Colors.RESET}")
        print(f"{Colors.GREEN}   启动完成！{Colors.RESET}")
        print(f"{Colors.CYAN}========================================{Colors.RESET}")
        print()
        print(f"   后端 API:  {Colors.CYAN}http://localhost:8000{Colors.RESET}")
        print(f"   前端页面: {Colors.CYAN}http://localhost:5173{Colors.RESET}")
        print(f"   API 文档: {Colors.CYAN}http://localhost:8000/docs{Colors.RESET}")
        print()

        atexit.register(cleanup, processes)

        webbrowser.open('http://localhost:5173')

        print(f"{Colors.RED}按 Ctrl+C 停止服务{Colors.RESET}")
        print()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print()
        cleanup(processes)
    except Exception as e:
        print(f"{Colors.RED}错误: {e}{Colors.RESET}")
        cleanup(processes)
        sys.exit(1)

if __name__ == '__main__':
    main()
