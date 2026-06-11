@echo off
setlocal
set PYTHONUTF8=1
set "PROJECT_ROOT=%~dp0"
set "PYTHONPATH=%PROJECT_ROOT%"
:: 可选：配置 AI 识别后端
:: mock | ollama | stepfun
:: set TAGGER_BACKEND=mock
:: set TAGGER_TIMEOUT_SECONDS=30
:: set TAGGER_MAX_KEYFRAMES=8
:: set OLLAMA_API_BASE=http://127.0.0.1:11434
:: set OLLAMA_MODEL=llava:7b
:: set STEPFUN_API_BASE=https://api.stepfun.com
:: set STEPFUN_API_KEY=your_api_key
:: set STEPFUN_MODEL=step-1v-8k
streamlit run app/main.py
endlocal
