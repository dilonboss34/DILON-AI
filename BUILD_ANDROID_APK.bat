@echo off
title JARVIS Mobile - GitHub Setup
color 0B
cls

echo.
echo  ===============================================
echo   JARVIS Mobile - Android APK Builder Setup
echo  ===============================================
echo.
echo  ئەم سکریپتە هەموو شت ئۆتۆماتیک دەکات:
echo  - پڕۆژەکەت دەنێرێت بۆ GitHub
echo  - APK خۆکار دروست دەبێت
echo  - ڕاستەوخۆ داونلۆد دەتوانیت
echo.
echo  ===============================================
echo.

REM Check git
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git دامەزراو نیە! 
    echo تکایە git لە https://git-scm.com داونلۆد بکە
    pause
    exit /b 1
)

echo [1/5] GitHub Username ی خۆت بنووسە:
echo (ئەو ئیمەیڵەی کە لێی تۆمار کردووتە لە github.com)
echo.
set /p GITHUB_USER="GitHub Username: "

echo.
echo [2/5] ناوی Repository ئەوەی ئەوێیت بیکەیت بنووسە:
echo (وەک: mark-xxxix یان jarvis-mobile)
set /p REPO_NAME="Repository Name: "

echo.
echo [3/5] پڕۆژەکە ئامادە دەکات...

cd /d "C:\Users\ggpsh\Desktop\Mark-XXXIX"

REM Initialize git if needed
if not exist ".git" (
    git init
    echo [OK] Git ئامادە کرا
)

REM Create .gitignore
echo __pycache__/ > .gitignore
echo *.pyc >> .gitignore
echo .buildozer/ >> .gitignore
echo .env >> .gitignore
echo *.log >> .gitignore
echo bin/ >> .gitignore
echo .kivy/ >> .gitignore

echo [4/5] فایلەکان زیاد دەکرێن...
git add .
git commit -m "JARVIS Mobile: Initial commit with Android build config" --allow-empty

echo.
echo [5/5] دیاریکردنی شاخی سەرەکی...
git branch -M main

echo.
echo ===============================================
echo  ئێستا پێویستە Repository بە دەستی دروست بکەیت
echo ===============================================
echo.
echo  1. ئەم لینکە بکەرەوە:
echo     https://github.com/new
echo.
echo  2. Repository Name: %REPO_NAME%
echo  3. هەڵبژێرە: Public
echo  4. هیچ شتێک تیک مەخە (README, gitignore, etc.)
echo  5. کلیک بکە لە "Create Repository"
echo.
echo  6. دوای ئەوەی Repository دروست کرد، Enter بکە تا بەردەوام ببین
echo.
pause

echo.
echo دانانی Remote...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git

echo.
echo نێردنی کۆدەکان بۆ GitHub...
echo (ئەگەر Username/Password پێیت داوا کرد، token ئەوەی دروست کردیت دابنێ)
echo.
git push -u origin main

if errorlevel 1 (
    echo.
    echo [ERROR] هەڵەیەک روویدا لە Push کردندا
    echo تکایە دڵنیاببەوە کە:
    echo  1. Repository دروست کراوە لە GitHub
    echo  2. ناوەکە ڕاستە: %REPO_NAME%
    echo  3. GitHub Token ی دروست هەیتە
    echo.
    echo بۆ دروستکردنی Token:
    echo  https://github.com/settings/tokens/new
    echo  هەڵبژێرە: repo (هەموو)
    echo.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo  ✅ سەرکەوتوو بوو!
echo ===============================================
echo.
echo  پڕۆژەکەت نێردرا بۆ GitHub!
echo  GitHub Actions دەستی کردووە بە دروستکردنی APK
echo.
echo  بۆ بینینی پرۆگرێسی دروستکردن:
echo  https://github.com/%GITHUB_USER%/%REPO_NAME%/actions
echo.
echo  دوای 15-20 خولەک APK ئامادە دەبێت لە:
echo  https://github.com/%GITHUB_USER%/%REPO_NAME%/releases
echo.
echo  ئەو لینکانەت بکەرەوە و APK ئامادەیە!
echo.

start https://github.com/%GITHUB_USER%/%REPO_NAME%/actions

pause
