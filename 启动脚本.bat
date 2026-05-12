@echo off
chcp 65001 >nul
echo ========================================
echo   Genshin Text Search 一键启动
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] 启动后端服务器...
cd "E:\Programming\some ideas\GenshinTextSearch\server"
call conda activate GenshinTextSearch
python server.py
