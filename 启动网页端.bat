@echo off
chcp 65001 >nul
setlocal
title 农文旅平台 - 网页端启动器
set "ROOT=%~dp0"

echo ==========================================================
echo   嘉兴乡村农文旅信息展示与服务平台 / 网页端
echo ----------------------------------------------------------
echo   启动后浏览器会自动打开：
echo     管理后台 : http://127.0.0.1:5173
echo     实时大屏 : http://127.0.0.1:5173/screen
echo   登录账号 : admin / admin123
echo ==========================================================
echo.

rem ---------- 1) 检查后端 ----------
powershell -NoProfile -ExecutionPolicy Bypass -Command "try{$r=Invoke-WebRequest 'http://127.0.0.1:5000/api/ping' -UseBasicParsing -TimeoutSec 3; if($r.StatusCode -eq 200){exit 0}else{exit 1}}catch{exit 1}"
if errorlevel 1 (
    echo [提示] 后端还没启动。
    echo        请先双击「启动后端服务.bat」，等它跑起来后再运行本文件。
    echo.
    pause
    exit /b 1
)
echo [1/4] 后端在线

rem ---------- 2) 定位 npm 的绝对路径 ----------
rem 必须用绝对路径：若只写 npm.cmd，cmd 传给 npm 的 %~dp0 会为空，
rem npm 就会去当前目录找 node_modules\npm\bin\npm-cli.js 从而报 MODULE_NOT_FOUND。
set "NPM="
set "NODEDIR="
for /f "delims=" %%i in ('where node.exe 2^>nul') do (
    if not defined NODEDIR set "NODEDIR=%%~dpi"
)
if defined NODEDIR if exist "%NODEDIR%npm.cmd" set "NPM=%NODEDIR%npm.cmd"
if not defined NPM if exist "D:\others\node.js\npm.cmd" set "NPM=D:\others\node.js\npm.cmd"
if not defined NPM (
    echo [错误] 没找到 npm.cmd，请先安装 Node.js 并确认 node 在 PATH 中。
    echo.
    pause
    exit /b 1
)
echo [2/4] npm 就绪

rem ---------- 3) 首次运行安装依赖 ----------
if not exist "%ROOT%web-frontend\node_modules" (
    echo [3/4] 首次运行，正在安装前端依赖，可能要几分钟 ...
    cd /d "%ROOT%web-frontend"
    call "%NPM%" install
    echo.
) else (
    echo [3/4] 依赖已存在，跳过安装
)

rem ---------- 4) 在新窗口启动 Vite ----------
echo [4/4] 正在新窗口启动 Vite ...
start "Vite :5173" cmd /k "cd /d %ROOT%web-frontend & call %NPM% run dev"

rem 等端口就绪后再开浏览器（最多等 40 秒）
echo.
echo 等待前端服务就绪 ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "for($i=0;$i -lt 80;$i++){try{$r=Invoke-WebRequest 'http://127.0.0.1:5173/' -UseBasicParsing -TimeoutSec 1; if($r.StatusCode -eq 200){exit 0}}catch{}; Start-Sleep -Milliseconds 500}; exit 1"
if errorlevel 1 (
    echo.
    echo [警告] 40 秒内没等到 5173 就绪，请查看新开的「Vite :5173」窗口里的报错。
) else (
    echo 前端已就绪，正在打开浏览器 ...
    start "" "http://127.0.0.1:5173"
)

echo.
echo ==========================================================
echo   前端已在「Vite :5173」窗口运行
echo   关闭那个窗口 = 停止前端；本窗口可以直接关闭
echo ==========================================================
echo.
pause
endlocal
