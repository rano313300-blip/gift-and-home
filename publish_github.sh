#!/usr/bin/env bash
# آپلود پروژه روی گیت‌هاب — ابتدا در github.com یک مخزن خالی بسازید و آدرسش را وارد کنید.
set -e
read -p "https://github.com/rano313300-blip/gift-and-home/tree/main " REPO
git init -b main
git config user.name "AMIR AMMARZAD"
read -p "rano313300-blip:" MAIL
git config user.email "$MAIL"
git add .
git commit -m "Initial commit: Dorhami store (Django) by AMIR AMMARZAD"
git remote add origin "$REPO"
git push -u origin main
