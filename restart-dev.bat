@echo off
chcp 65001 >nul
title Blog Dev Server Restart
echo ==========================================
echo  Blog 开发服务器 一键重启
echo ==========================================
echo.
echo  将结束占用 5000 端口的进程和所有 python.exe
echo  如果你同时运行着其他 Python 程序，请先保存！
echo.
choice /c YN /n /m "确认继续? [Y/N] "
if errorlevel 2 exit /b
echo.
echo [1/2] 清理占用 5000 的进程与残留 python.exe ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo   已结束 PID %%a
)
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul
echo [2/2] 启动开发服务器  http://127.0.0.1:5000 ...
cd /d "%~dp0"
python main.py
echo.
echo 服务器已退出。按任意键关闭窗口...
pause >nul
