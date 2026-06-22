@echo off
echo ==============================================
echo       Create a New Release / Patch
echo ==============================================
echo.

set /p version="Enter new version number (e.g., v1.1.0): "
if "%version%"=="" (
    echo Version cannot be empty!
    pause
    exit /b
)

set /p message="Enter release notes/message: "
if "%message%"=="" set message=Release %version%

echo.
echo 1. Syncing latest code before release...
git add .
git commit -m "chore: prep release %version%"
git push origin master

echo.
echo 2. Creating Release Tag (%version%)...
git tag -a %version% -m "%message%"
git push origin %version%

echo.
echo ==============================================
echo Release %version% successfully pushed to GitHub!
echo Users can now download this specific version.
echo ==============================================
pause
