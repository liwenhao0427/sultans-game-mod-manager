@echo off
set json={"name":"Alice","age":25}
for /f "delims=" %%i in ('powershell -command "%json% | ConvertFrom-Json | Select -ExpandProperty name"') do (
    set name=%%i
)
echo Name: %name%
pause
