@echo off
chcp 65001 >nul
set /p REPO=https://github.com/rano313300-blip/gift-and-home/tree/main
set /p MAIL= rano313300-blip:
git init -b main
git config user.name "AMIR AMMARZAD"
git config user.email "%MAIL%"
git add .
git commit -m "Initial commit: Dorhami store (Django) by AMIR AMMARZAD"
git remote add origin %REPO%
git push -u origin main
pause
