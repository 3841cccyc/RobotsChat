# 机器人对话系统 - 一键启动脚本 (PowerShell版)
# 使用方法: 右键 -> "使用 PowerShell 运行"

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   机器人对话系统 - 一键启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] 检查环境变量..." -ForegroundColor Yellow

if (-not $env:MINIMAX_API_KEY) {
    Write-Host "   错误: 未设置 MINIMAX_API_KEY 环境变量" -ForegroundColor Red
    Write-Host "   请在系统环境变量中设置:" -ForegroundColor Yellow
    Write-Host "   Windows: [系统设置] -> [环境变量] -> 新建系统变量" -ForegroundColor White
    Write-Host "   或在当前终端: `$env:MINIMAX_API_KEY=`"你的API密钥`"" -ForegroundColor White
    Write-Host ""
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "   MINIMAX_API_KEY 已设置 ✓" -ForegroundColor Green

Write-Host ""
Write-Host "[2/3] 启动后端服务..." -ForegroundColor Yellow

$BackendJob = Start-Job -ScriptBlock {
    param($path, $apiKey)
    Set-Location $path
    $env:MINIMAX_API_KEY = $apiKey
    & "..\.venv\Scripts\Activate.ps1"
    python -m app.main
} -ArgumentList (Resolve-Path "backend"), $env:MINIMAX_API_KEY

Write-Host "   后端已启动 (Job ID: $($BackendJob.Id))" -ForegroundColor Green

Write-Host ""
Write-Host "[3/3] 启动前端服务..." -ForegroundColor Yellow

$FrontendJob = Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    npm run dev
} -ArgumentList (Resolve-Path "frontend")

Write-Host "   前端已启动 (Job ID: $($FrontendJob.Id))" -ForegroundColor Green

Write-Host ""
Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   后端 API:  http://localhost:8000" -ForegroundColor White
Write-Host "   前端页面: http://localhost:5173" -ForegroundColor White
Write-Host "   API 文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "   正在打开浏览器..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "如需停止服务，请运行以下命令:" -ForegroundColor Red
Write-Host "   Stop-Job -Id $($BackendJob.Id), $($FrontendJob.Id)" -ForegroundColor Red
Write-Host "   Remove-Job -Id $($BackendJob.Id), $($FrontendJob.Id)" -ForegroundColor Red
Write-Host ""

Read-Host "按回车键退出 (服务将在后台继续运行)"
