@echo off
echo ========================================
echo    YouTubeShortsAuto - Web UI
echo ========================================
echo.
echo Iniciando servidor web...
echo Abre tu navegador en: http://localhost:8501
echo.
py -m streamlit run web.py --server.port 8501
pause
