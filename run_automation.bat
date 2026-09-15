@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_EXE=python
) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON_EXE="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else (
    set PYTHON_EXE=python
)

if not exist "logs" mkdir "logs"

echo ====================================================== >> logs\scheduler.log
echo [TASK LAUNCHER] Starting at %DATE% %TIME% >> logs\scheduler.log
echo [TASK LAUNCHER] Arguments: %* >> logs\scheduler.log

%PYTHON_EXE% run.py %* >> logs\scheduler.log 2>&1

set EXIT_CODE=%ERRORLEVEL%
echo [TASK LAUNCHER] Finished with exit code %EXIT_CODE% at %DATE% %TIME% >> logs\scheduler.log
echo ====================================================== >> logs\scheduler.log

exit /b %EXIT_CODE%
