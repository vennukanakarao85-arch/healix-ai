@echo off
title HEALIX AI - FULL SYSTEM
color 0B
echo ---------------------------------------------------
echo  STARTING HEALIX AI PORTAL...
echo ---------------------------------------------------
echo.
echo  1. Launching Dashboard Server...
start "Healix App" cmd /k "python app.py"
timeout /t 5 >nul

echo  2. Starting Robust Public Tunnel...
start "Healix Tunnel" cmd /k "python start_ngrok.py"

echo.
echo ---------------------------------------------------
echo  SYSTEM READY!
echo  - Shared access enabled via ngrok.
echo  - Cloud files (Procfile) are ready for Render.
echo ---------------------------------------------------
pause
