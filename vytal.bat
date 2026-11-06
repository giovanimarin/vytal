@echo off
rem Bypass applies only to this process; no machine policy or firewall changes.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0vytal.ps1" %*
exit /b %errorlevel%
