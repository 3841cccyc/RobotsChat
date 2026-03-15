#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 对话系统启动脚本
功能：
  - 自动检查环境配置
  - 检查系统环境变量 MINIMAX_API_KEY
  - 安装前后端依赖
  - 启动后端和前端服务
  - 自动打开浏览器

注意：MINIMAX_API_KEY 需要通过系统环境变量设置

用法：
  python start.py        启动所有服务
  python start.py start  启动所有服务
  python start.py stop   停止所有服务
  python start.py restart 重启所有服务
  python start.py status 查看服务状态
"""

import os
import sys
import subprocess
import time
import signal
import socket
import platform
from pathlib import Path
from typing import Optional, List

# ============== 配置 ==============
PROJECT_ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
ENV_FILE = BACKEND_DIR / ".env"
ENV_EXAMPLE = BACKEND_DIR / ".env.example"
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = BACKEND_DIR / "requirements.txt"
PACKAGE_JSON = FRONTEND_DIR / "package.json"

BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = 8000
FRONTEND_PORT = 5173

# 全局进程存储
processes: List[subprocess.Popen] = []

# Windows 标志
IS_WINDOWS = platform.system() == "Windows"


def print_info(msg: str):
    """打印信息"""
    print(f"\033[94m[信息]\033[0m {msg}")


def print_success(msg: str):
    """打印成功"""
    print(f"\033[92m[成功]\033[0m {msg}")


def print_warning(msg: str):
    """打印警告"""
    print(f"\033[93m[警告]\033[0m {msg}")


def print_error(msg: str):
    """打印错误"""
    print(f"\033[91m[错误]\033{0m {msg}")


def run_command(cmd: List[str], cwd: Optional[Path] = None, env: Optional[dict] = None, shell: bool = False) -> subprocess.CompletedProcess:
    """运行命令并返回结果"""
    if shell and IS_WINDOWS:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
        return subprocess.run(cmd_str, cwd=cwd, env=env, shell=True, capture_output=True, text=True)
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def check_command(cmd: str) -> bool:
    """检查命令是否存在"""
    if IS_WINDOWS:
        result = subprocess.run(f"where {cmd}", shell=True, capture_output=True, text=True)
    else:
        result = subprocess.run(f"which {cmd}", shell=True, capture_output=True, text=True)
    return result.returncode == 0


def get_command_path(cmd: str) -> Optional[str]:
    """获取命令路径"""
    if IS_WINDOWS:
        result = subprocess.run(f"where {cmd}", shell=True, capture_output=True, text=True)
    else:
        result = subprocess.run(f"which {cmd}", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip().split("\n")[0]
    return None


def check_python_version() -> bool:
    """检查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 版本过低！当前: {version.major}.{version.minor}, 需要: 3.8+")
        return False
    print_info(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True


def check_node_version() -> bool:
    """检查 Node.js 版本"""
    if not check_command("node"):
        print_error("未找到 Node.js，请先安装 Node.js")
        return False

    result = run_command(["node", "--version"])
    version = result.stdout.strip()
    print_info(f"Node.js 版本: {version}")
    return True


def check_npm_version() -> bool:
    """检查 npm 版本"""
    if not check_command("npm"):
        print_error("未找到 npm，请先安装 Node.js")
        return False

    result = run_command(["npm", "--version"])
    version = result.stdout.strip()
    print_info(f"npm 版本: {version}")
    return True


def check_env_variable() -> bool:
    """检查系统环境变量 MINIMAX_API_KEY"""
    api_key = os.environ.get("MINIMAX_API_KEY", "")

    if api_key and api_key != "your-minimax-api-key-here":
        # 隐藏部分 key 显示
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print_info(f"MINIMAX_API_KEY: {masked_key}")
        return True
    else:
        print_warning("未设置系统环境变量 MINIMAX_API_KEY")
        print_info("请在运行脚本前设置环境变量:")
        if IS_WINDOWS:
            print_info("  set MINIMAX_API_KEY=your-api-key")
            print_info("  或在 PowerShell 中:")
            print_info("  $env:MINIMAX_API_KEY='your-api-key'")
        else:
            print_info("  export MINIMAX_API_KEY=your-api-key")
        return False


def ensure_venv() -> bool:
    """确保虚拟环境存在"""
    if VENV_DIR.exists():
        print_info("虚拟环境已存在")
        return True

    print_info("创建虚拟环境...")
    result = run_command([sys.executable, "-m", "venv", str(VENV_DIR)])
    if result.returncode != 0:
        print_error(f"创建虚拟环境失败: {result.stderr}")
        return False

    print_success("虚拟环境创建成功")
    return True


def get_venv_python() -> Path:
    """获取虚拟环境中的 Python 解释器路径"""
    if IS_WINDOWS:
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def install_backend_deps() -> bool:
    """安装后端依赖"""
    python = get_venv_python()

    if not python.exists():
        print_error("虚拟环境 Python 不存在")
        return False

    # 检查是否已安装依赖
    result = run_command([str(python), "-c", "import fastapi"], capture_output=True)
    if result.returncode == 0:
        print_info("后端依赖已安装")
        return True

    print_info("安装后端依赖...")

    # 升级 pip
    result = run_command([str(python), "-m", "pip", "install", "--upgrade", "pip"],
                         capture_output=True)
    if result.returncode != 0:
        print_warning(f"升级 pip 失败: {result.stderr}")

    # 安装依赖
    result = run_command([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
                         capture_output=True)
    if result.returncode != 0:
        print_error(f"安装后端依赖失败: {result.stderr}")
        return False

    print_success("后端依赖安装成功")
    return True


def install_frontend_deps() -> bool:
    """安装前端依赖"""
    # 检查是否已有 node_modules
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        print_info("前端依赖已安装")
        return True

    print_info("安装前端依赖...")
    result = run_command(["npm", "install"], cwd=FRONTEND_DIR)
    if result.returncode != 0:
        print_error(f"安装前端依赖失败: {result.stderr}")
        return False

    print_success("前端依赖安装成功")
    return True


def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except:
            return True


def wait_for_service(port: int, timeout: int = 30) -> bool:
    """等待服务启动"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(1)
        if is_port_in_use(port):
            return True
    return False


def kill_process_on_port(port: int):
    """杀死占用指定端口的进程"""
    if IS_WINDOWS:
        # Windows: 使用 netstat 找到进程并杀死
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True, capture_output=True, text=True
        )
        for line in result.stdout.strip().split("\n"):
            if "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    subprocess.run(f'taskkill /PID {pid} /F', shell=True)
                    print_info(f"已终止占用端口 {port} 的进程 (PID: {pid})")
    else:
        # Unix: 使用 lsof 或 fuser
        result = subprocess.run(f"lsof -ti:{port}", shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                subprocess.run(f"kill -9 {pid}", shell=True)
                print_info(f"已终止占用端口 {port} 的进程 (PID: {pid})")


def start_backend() -> Optional[subprocess.Popen]:
    """启动后端服务"""
    if is_port_in_use(BACKEND_PORT):
        print_warning(f"后端端口 {BACKEND_PORT} 已被占用，尝试终止...")
        kill_process_on_port(BACKEND_PORT)
        time.sleep(1)

    print_info("启动后端服务...")

    python = get_venv_python()
    backend_main = BACKEND_DIR / "app" / "main.py"

    # 获取 API Key
    api_key = os.environ.get("MINIMAX_API_KEY", "")

    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    if api_key:
        env["MINIMAX_API_KEY"] = api_key

    if IS_WINDOWS:
        # Windows: 使用 start 命令在新窗口启动，需要显式传递环境变量
        if api_key:
            cmd = f'start "Backend API - {BACKEND_PORT}" cmd /k "set MINIMAX_API_KEY={api_key} && {python} -m uvicorn app.main:app --host {BACKEND_HOST} --port {BACKEND_PORT} --reload"'
        else:
            cmd = f'start "Backend API - {BACKEND_PORT}" cmd /k "{python} -m uvicorn app.main:app --host {BACKEND_HOST} --port {BACKEND_PORT} --reload"'
        subprocess.Popen(cmd, shell=True, cwd=BACKEND_DIR, env=env)
        processes.append(None)  # 占位
    else:
        # Unix: 后台运行
        proc = subprocess.Popen(
            [str(python), "-m", "uvicorn", "app.main:app", "--host", BACKEND_HOST, "--port", str(BACKEND_PORT), "--reload"],
            cwd=BACKEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(proc)

    print_info("后端服务启动中...")
    return processes[-1]


def start_frontend() -> Optional[subprocess.Popen]:
    """启动前端服务"""
    if is_port_in_use(FRONTEND_PORT):
        print_warning(f"前端端口 {FRONTEND_PORT} 已被占用，尝试终止...")
        kill_process_on_port(FRONTEND_PORT)
        time.sleep(1)

    print_info("启动前端服务...")

    if IS_WINDOWS:
        # Windows: 使用 start 命令在新窗口启动
        cmd = f'start "Frontend - {FRONTEND_PORT}" cmd /k "npm run dev"'
        subprocess.Popen(cmd, shell=True, cwd=FRONTEND_DIR)
        processes.append(None)  # 占位
    else:
        # Unix: 后台运行
        proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(proc)

    print_info("前端服务启动中...")
    return processes[-1]


def open_browser():
    """打开浏览器"""
    import webbrowser
    url = f"http://localhost:{FRONTEND_PORT}"
    print_info(f"打开浏览器: {url}")
    webbrowser.open(url)


def stop_services():
    """停止所有服务"""
    print_info("停止所有服务...")

    # 杀死占用端口的进程
    if is_port_in_use(BACKEND_PORT):
        kill_process_on_port(BACKEND_PORT)

    if is_port_in_use(FRONTEND_PORT):
        kill_process_on_port(FRONTEND_PORT)

    print_success("所有服务已停止")


def check_status() -> bool:
    """检查服务状态"""
    backend_running = is_port_in_use(BACKEND_PORT)
    frontend_running = is_port_in_use(FRONTEND_PORT)

    print("\n" + "=" * 40)
    print("           服务状态")
    print("=" * 40)

    backend_status = "\033[92m运行中\033[0m" if backend_running else "\033[91m已停止\033[0m"
    frontend_status = "\033[92m运行中\033[0m" if frontend_running else "\033[91m已停止\033[0m"

    print(f"后端 API: {backend_status} (端口 {BACKEND_PORT})")
    print(f"前端页面: {frontend_status} (端口 {FRONTEND_PORT})")

    if backend_running:
        print(f"  API 文档: http://localhost:{BACKEND_PORT}/docs")
    if frontend_running:
        print(f"  访问地址: http://localhost:{FRONTEND_PORT}")

    print("=" * 40)

    return backend_running and frontend_running


def print_banner():
    """打印横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║         🤖 AI 对话系统 - 启动脚本                            ║
║                                                           ║
║  后端: http://localhost:8000                              ║
║  前端: http://localhost:5173                               ║
║  API文档: http://localhost:8000/docs                      ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def main():
    """主函数"""
    # 解析命令行参数
    command = sys.argv[1] if len(sys.argv) > 1 else "start"

    if command == "stop":
        stop_services()
        return

    if command == "status":
        check_status()
        return

    if command == "restart":
        stop_services()
        time.sleep(2)
        main()
        return

    if command not in ("start", ""):
        print_error(f"未知命令: {command}")
        print("用法: python start.py [start|stop|restart|status]")
        sys.exit(1)

    # 开始启动流程
    print_banner()

    # 1. 检查环境
    print_info("=" * 50)
    print_info("步骤 1: 检查环境")
    print_info("=" * 50)

    if not check_python_version():
        sys.exit(1)

    if not check_node_version():
        sys.exit(1)

    if not check_npm_version():
        sys.exit(1)

    # 2. 检查环境变量
    print_info("=" * 50)
    print_info("步骤 2: 检查环境变量")
    print_info("=" * 50)

    env_ok = check_env_variable()
    if not env_ok:
        print_warning("服务可以启动，但 AI 对话功能需要有效的 MINIMAX_API_KEY")

    # 3. 安装依赖
    print_info("=" * 50)
    print_info("步骤 3: 安装依赖")
    print_info("=" * 50)

    if not ensure_venv():
        sys.exit(1)

    if not install_backend_deps():
        sys.exit(1)

    if not install_frontend_deps():
        sys.exit(1)

    # 4. 启动服务
    print_info("=" * 50)
    print_info("步骤 4: 启动服务")
    print_info("=" * 50)

    # 启动后端
    start_backend()
    time.sleep(2)

    # 启动前端
    start_frontend()

    # 等待服务启动
    print_info("等待服务启动...")

    backend_ok = wait_for_service(BACKEND_PORT, timeout=15)
    frontend_ok = wait_for_service(FRONTEND_PORT, timeout=15)

    print("\n" + "=" * 50)
    if backend_ok and frontend_ok:
        print_success("所有服务启动成功!")
    else:
        if not backend_ok:
            print_warning(f"后端服务可能未正常启动 (端口 {BACKEND_PORT})")
        if not frontend_ok:
            print_warning(f"前端服务可能未正常启动 (端口 {FRONTEND_PORT})")
    print("=" * 50)

    # 打开浏览器
    time.sleep(1)
    open_browser()

    print("\n" + "=" * 50)
    print("服务已启动，按 Ctrl+C 可停止所有服务")
    print("=" * 50)

    # 等待用户中断
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n")
        stop_services()
        print_success("已退出")


if __name__ == "__main__":
    main()
