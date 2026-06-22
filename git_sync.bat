@echo off
echo ==============================================
echo          Risore - Git Auto Sync
echo ==============================================
echo.

set /p commit_msg="Enter commit message (or press Enter for 'Auto-sync update'): "
if "%commit_msg%"=="" set commit_msg=Auto-sync update

echo.
echo Syncing with GitHub...
git add .
git commit -m "%commit_msg%"
git push origin master

echo.
echo ==============================================
echo   Sync Complete! Changes pushed to GitHub.
echo ==============================================
pause
