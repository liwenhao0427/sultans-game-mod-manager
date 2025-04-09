chcp 65001
@echo off
setlocal enabledelayedexpansion

echo 正在还原MOD文件...
set "bak_dir=Sultan's Game_Data\\StreamingAssets\\config\\bak"
set "config_dir=Sultan's Game_Data\\StreamingAssets\\config"
set "restored=0"
set "deleted=0"

:: 递归处理bak目录
for /r "%bak_dir%" %%f in (*.bak) do (
    set "bak_file=%%f"
    set "relative_path=%%~pnxf"
    set "relative_path=!relative_path:~0,-4!"
    set "target_file=%config_dir%!relative_path!"

    :: 检查是否是ADD标记(空文件)
    for %%s in ("%%f") do set "size=%%~zs"
    if !size! equ 1 (
        if exist "!target_file!" (
            echo 删除ADD创建的文件: !target_file!
            del "!target_file!"
            set /a "deleted+=1"
        )
    ) else (
        if exist "!target_file!" (
            echo 恢复文件: !target_file!
            move /y "!bak_file!" "!target_file!" >nul
            set /a "restored+=1"
        ) else (
            echo 原始文件不存在: !target_file!
        )
    )
)

:: 清理空目录
for /f "delims=" %%d in ('dir /s /b /ad "%bak_dir%" ^| sort /r') do (
    rd "%%d" 2>nul
)

echo ----------
if !restored! gtr 0 (
    echo 已恢复 !restored! 个文件
) else (
    echo 没有需要恢复的文件
)

if !deleted! gtr 0 (
    echo 已删除 !deleted! 个ADD创建的文件
) else (
    echo 没有ADD创建的文件需要删除
)

