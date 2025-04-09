@echo off
chcp 65001 > nul

:: 删除public/Mods目录（无论是真实目录还是符号链接）
if exist "public\Mods" (
    rmdir /s /q "public\Mods"
)

:: 创建public/Mods目录并复制所有文件
xcopy /e /i /y "src\assets\Mods" "public\Mods\"

echo 文件已从src/assets/Mods复制到public/Mods
pause
