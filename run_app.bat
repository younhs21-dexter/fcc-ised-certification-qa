@echo off
echo ====================================
echo FCC/ISED Q&A System Starting...
echo ====================================
echo.
echo Web UI will open at: http://localhost:8501
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
python -m streamlit run app.py --server.headless true
pause
