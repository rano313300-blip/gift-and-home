#!/usr/bin/env bash
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations shop
python manage.py migrate
python manage.py seed_products
echo "===== حالا حساب مدیر را بسازید ====="
python manage.py createsuperuser
echo "اجرای سایت: http://127.0.0.1:8000"
python manage.py runserver
