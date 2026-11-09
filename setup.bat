@echo off
title SmartAttend AI Setup
python --version
if errorlevel 1 (
  echo Install Python 3.11 from https://www.python.org/downloads/
  pause
  exit /b 1
)
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo Installation failed.
  pause
  exit /b 1
)
echo Setup completed successfully.
pause
