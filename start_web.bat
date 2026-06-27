@echo off
echo ==============================================
echo       Starting Risore AI Web Platform...
echo ==============================================
echo.

echo Launching Web Browser...
start http://localhost:8000/

echo.
echo Server is running! Keep this window open.
echo (Press Ctrl+C to stop the server)
echo.

venv\Scripts\python.exe server.py
