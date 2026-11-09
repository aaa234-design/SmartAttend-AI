@echo off
title SmartAttend AI
if not exist .venv\Scripts\activate.bat (
  echo Please run setup.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate
streamlit run app.py
pause
