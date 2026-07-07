@echo off
echo 🐂 基金投资追踪 Dashboard
echo =============================
echo.
echo 启动本地服务器...
cd /d "%~dp0"
start "" "http://localhost:8899"
python -m http.server 8899
