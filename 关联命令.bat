@echo off
chcp 65001 > nul
echo 正在设置Mods目录符号链接...

:: 删除public/Mods目录（无论是真实目录还是符号链接）
if exist "public\Mods" (
    echo 正在删除现有的public\Mods...
    rmdir /s /q "public\Mods"
    if exist "public\Mods" (
        echo 删除失败，请以管理员身份运行此脚本
        pause
        exit /b 1
    )
    echo 已成功删除原有目录
)

:: 创建新的符号链接
echo 正在创建新的符号链接...
mklink /d "C:\Users\Administrator\IdeaProjects\sultans-game-mod-manager\public\Mods" "C:\Users\Administrator\IdeaProjects\sultans-game-mod-manager\src\assets\Mods"

if errorlevel 1 (
    echo 创建符号链接失败，请以管理员身份运行此脚本
) else (
    echo 符号链接创建成功！
    echo public\Mods -> src\assets\Mods
)

pause
