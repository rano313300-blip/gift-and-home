@echo off
chcp 65001 >nul
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations shop
python manage.py migrate
python manage.py seed_products
echo.
echo ===== حالا حساب مدیر را بسازید =====
python manage.py createsuperuser
echo.
echo اجرای سایت: http://127.0.0.1:8000
python manage.py runserver
