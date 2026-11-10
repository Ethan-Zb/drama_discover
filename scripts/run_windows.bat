@echo off
chcp 65001 >nul
call .venv\Scripts\activate
python manage.py runserver
