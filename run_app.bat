@echo off
title Healix AI Server
color 0E
echo ---------------------------------------------------
echo  STARTING HEALIX AI SERVER...
echo  Please wait...
echo ---------------------------------------------------
cd /d "%~dp0"
python app.py
pause
