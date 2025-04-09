@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ======================================
echo           MOD还原工具
echo ======================================

set "bak_dir=%~dp0Sultan's Game_Data\StreamingAssets\config\bak"
set "config_dir=%~dp0Sultan's Game_Data\StreamingAssets\config"
set "restored=0"
set "deleted=0"
set "errors=0"

if not exist "!bak_dir!" (
    echo 备份目录不存在，没有需要还原的MOD
    echo ======================================
    exit /b 0
)

:: 递归处理bak目录
for /r "!bak_dir!" %%f in (*.bak) do (
    set "bak_file=%%f"
    
    :: 确定目标文件路径
    set "rel_path=%%~pf"
    set "rel_path=!rel_path:%bak_dir%\=!"
    set "target_file=!config_dir!\!rel_path!%%~nf"
    
    :: 检查是否是ADD标记(空文件)
    for %%s in ("%%f") do set "size=%%~zs"
    if !size! leq 3 (
        if exist "!target_file!" (
            echo [删除] !target_file!
            del "!target_file!" 2>nul
            if !errorlevel! equ 0 (
                set /a "deleted+=1"
            ) else (
                set /a "errors+=1"
                echo   X 删除失败
            )
        )
    ) else (
        if exist "!target_file!" (
            echo [还原] !target_file!
            copy /y "!bak_file!" "!target_file!" >nul
            if !errorlevel! equ 0 (
                set /a "restored+=1"
            ) else (
                set /a "errors+=1"
                echo   X 还原失败
            )
        ) else (
            echo [跳过] !bak_file! - 目标文件不存在
        )
    )
    
    :: 删除备份文件
    del "!bak_file!" 2>nul
)

:: 清理空目录
for /f "delims=" %%d in ('dir /s /b /ad "!bak_dir!" ^| sort /r') do (
    rd "%%d" 2>nul
)

echo ======================================
echo 还原完成!
echo   还原: !restored! 个文件
echo   删除: !deleted! 个文件
if !errors! gtr 0 (
    echo   错误: !errors! 个操作失败
)
echo ======================================

exit /b 0
