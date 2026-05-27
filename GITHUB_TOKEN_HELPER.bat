@echo off
title JARVIS Mobile - GitHub Token Helper
color 0B
cls

echo.
echo  ===============================================
echo   GitHub Token دروستکردن - ئاسانترین ڕێگا
echo  ===============================================
echo.
echo  تکایە ئەم هەنگاوانە بکە:
echo.
echo  [1] ئەم لینکە دەکرێتەوە خۆکار...
echo      github.com/settings/tokens/new
echo.
echo  [2] لەو شتانەی دەبینیت:
echo      - Note: دابنێ "JARVIS Mobile Build"
echo      - Expiration: هەڵبژێرە "No expiration"
echo      - لە بەشی Select scopes:
echo        ✅ repo  (هەموو تیک بکە)
echo        ✅ workflow
echo.
echo  [3] کلیک بکە "Generate Token" (خوارەوە)
echo.
echo  [4] Token ئامادە دەبێت - کۆپی بکە (تەنها یەک جار دەبینیتەوە!)
echo.
echo  [5] کاتێک Push دەکەیت:
echo      Username: ئیمەیڵ یان ناوی GitHub ی خۆت
echo      Password: ئەو Token ئەوەی کۆپیت کرد (نەک پاسوۆردی ئاسایی)
echo.
echo ===============================================
echo.
start https://github.com/settings/tokens/new
pause
