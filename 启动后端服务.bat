@echo off
chcp 65001 >nul
setlocal
title 农文旅平台 - 后端服务 (:5000)
set "ROOT=%~dp0"

echo ==========================================================
echo   嘉兴乡村农文旅信息展示与服务平台 / 后端服务
echo ----------------------------------------------------------
echo   可以用浏览器打开（健康检查）:
echo     http://127.0.0.1:5000/api/ping
echo ----------------------------------------------------------
echo   下面这两个【不要】用浏览器打开，报错属于正常:
echo     POST /api/auth/login     登录接口，浏览器打开会提示 405
echo     ws://127.0.0.1:5000/ws   实时通道，只给程序连接
echo ----------------------------------------------------------
echo   平台界面请双击「启动网页端.bat」，然后访问:
echo     http://127.0.0.1:5173    登录账号 admin / admin123
echo ==========================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 没找到 python 命令，请先安装 Python 3 或把它加入 PATH。
    echo.
    pause
    exit /b 1
)

netstat -ano | findstr ":6379" | findstr "LISTENING" >nul
if errorlevel 1 (
    if exist "%ROOT%tools\redis\redis-server.exe" (
        echo [1/2] 启动 Redis ...
        start "Redis :6379" /min "%ROOT%tools\redis\redis-server.exe" --port 6379 --bind 127.0.0.1 --save 3600 1
        ping -n 3 127.0.0.1 >nul
    ) else (
        echo [1/2] 未找到 tools\redis\redis-server.exe，跳过 Redis（功能不受影响，只是没有缓存）
    )
) else (
    echo [1/2] Redis 已在运行，跳过
)

echo [2/2] 启动 Flask 后端 ...
echo.
set "PYTHONIOENCODING=utf-8"
cd /d "%ROOT%web-backend"
python app.py

echo.
echo [后端已退出] 如果上方有报错，把窗口内容截图保存即可。
pause
endlocal
