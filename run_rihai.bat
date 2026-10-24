@echo off
rem Rihai one-click launcher (Windows). Double-click this file.
rem First run installs the dependencies; later runs just start the app.
cd /d "%~dp0"
where python >nul 2>&1 || (echo Python is not installed. Install Python 3.10+ from python.org, tick "Add to PATH", then run this again. & pause & exit /b 1)
python -c "import streamlit, dateutil, pandas" >nul 2>&1 || (echo Installing Rihai's dependencies, one time... & python -m pip install -q -r requirements.txt)
echo.
echo Starting Rihai. A browser tab will open. Close this window to stop.
echo.
python -m streamlit run rihai\app\streamlit_app.py --server.headless false --browser.gatherUsageStats false
pause
