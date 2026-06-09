@echo off
setlocal
set PYTHONUTF8=1
set "PROJECT_ROOT=%~dp0"
set "PYTHONPATH=%PROJECT_ROOT%"
streamlit run app/main.py
endlocal
