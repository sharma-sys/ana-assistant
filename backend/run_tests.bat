@echo off
echo Activating virtual environment and running tests...
call venv\Scripts\activate.bat
python -m pytest
echo.
pause
