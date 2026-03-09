@echo off
chcp 65001 >nul
title 机器人对话系统启动器

echo ========================================
echo    机器人对话系统 - 一键启动
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查环境变量...
if "%MINIMAX_API_KEY%"=="" (
    echo     警告: 系统未设置 MINIMAX_API_KEY 环境变量
    echo     请在系统环境变量中设置:
    echo     MINIMAX_API_KEY=你的API密钥
    echo.
    pause
    exit /b 1
)

echo     MINIMAX_API_KEY 已设置 ✓
echo.

echo [2/3] 启动后端服务...
start "Backend - FastAPI" cmd /k "cd /d "%~dp0backend" && call ..\.venv\Scripts\activate.bat && python -m app.main"

echo.
echo [3/3] 启动前端服务...
start "Frontend - Vite" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo 等待服务启动...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo    启动完成！
echo ========================================
echo.
echo   后端 API:  http://localhost:8000
echo   前端页面: http://localhost:5173
echo   API 文档: http://localhost:8000/docs
echo.
echo   按任意键打开浏览器...
echo   关闭此窗口不会停止服务
echo.
pause >nul

start http://localhost:5173
