@echo off
chcp 65001 >nul
echo Creating virtual environment...
py -3.12 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Dependencies installed.
echo Next: create the MySQL database, edit .env, then run migrate.
pause
