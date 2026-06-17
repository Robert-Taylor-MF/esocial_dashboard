@echo off
cd /d "%~dp0"
call venv\Scripts\activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0