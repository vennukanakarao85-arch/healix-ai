@echo off
title Healix AI - START ALL
color 0E

echo ---------------------------------------------------
echo  STARTING HEALIX AI (Full System)
echo ---------------------------------------------------
echo.
echo  1. Launching Application Server...
start "Healix App" cmd /k "run_app.bat"
timeout /t 3 >nul

echo  2. Launching Public Tunnel...
start "Healix Tunnel" cmd /k "start_public_access.bat"

echo.
echo ---------------------------------------------------
echo  SYSTEM STARTED!
echo  - Keep both black windows open.
echo  - Look at the Tunnel window for your Public URL.
echo ---------------------------------------------------
pause
