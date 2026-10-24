@echo off
setlocal
cd /d "%~dp0"
for %%F in ("tools\upx.exe" "dgvoodoo\D3D8.dll" "dgvoodoo\dgVoodoo.conf" "cursorfix\visique_cursor.dll") do (
  if not exist %%F (
    echo ERROR: %%~F is missing.
    exit /b 1
  )
)
py -m PyInstaller --clean --noconfirm "VISIQUE-Luxor-Fix.spec"
if errorlevel 1 exit /b 1
echo.
echo Build complete: dist\VISIQUE-Luxor-Fix.exe
