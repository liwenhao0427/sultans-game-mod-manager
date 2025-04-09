@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ======================================
echo           MOD安装管理工具
echo ======================================

:: 检查sed工具
if not exist "%~dp0sed.exe" (
    echo 错误：需要将sed.exe与本脚本放在同一目录
    pause
    exit /b 1
)

:: 第一步：执行还原操作
echo [预处理] 正在执行还原操作...
call "%~dp0还原mod.bat"
if %errorlevel% neq 0 (
    echo 还原操作失败，安装中止
    pause
    exit /b 1
)

:: 创建备份目录
set "bak_dir=%~dp0Sultan's Game_Data\StreamingAssets\config\bak"
if not exist "!bak_dir!" (
    mkdir "!bak_dir!"
)

:: 第二步：安装MOD
echo [安装阶段] 开始处理MOD文件...

:: 设置计数器
set "total_mods=0"
set "success_mods=0"
set "skipped_mods=0"
set "failed_mods=0"

:: 递归处理Mods目录
for /r "%~dp0Mods" %%f in (*.json) do (
    set /a "total_mods+=1"

    set "json_file=%%f"
    set "config_file=%%~dpnf.config"

    echo [读取配置文件] !config_file!

    :: 检查配置文件是否存在
    if exist "!config_file!" (
        echo [处理] !json_file!
        call :process_mod "!json_file!" "!config_file!"
        if !errorlevel! equ 0 (
            set /a "success_mods+=1"
        ) else if !errorlevel! equ 1 (
            set /a "skipped_mods+=1"
        ) else (
            set /a "failed_mods+=1"
        )
    ) else (
        echo [跳过] !json_file! - 找不到配置文件
        set /a "skipped_mods+=1"
    )
)

echo ======================================
echo 安装完成! 总计: !total_mods! 个MOD
echo   成功: !success_mods!
echo   跳过: !skipped_mods!
echo   失败: !failed_mods!
echo ======================================
pause
exit /b 0

:process_mod
set "source_file=%~1"
set "config_file=%~2"
set "error_level=0"

:: 读取配置文件
set "mode="
set "target_path="
set "val1="
set "val2="

set /a line_num=0
for /f "usebackq tokens=* delims=" %%a in ("%config_file%") do (
    set /a line_num+=1
    if !line_num! equ 1 set "mode=%%a"
    if !line_num! equ 2 set "target_path=%%a"
    if !line_num! equ 3 set "val1=%%a"
    if !line_num! equ 4 set "val2=%%a"
)

:: 设置目标文件完整路径
set "target_file=%~dp0Sultan's Game_Data\StreamingAssets\config\!target_path!"

:: 为备份创建目录结构
set "bak_file=!bak_dir!\!target_path!.bak"
for %%a in ("!bak_file!") do (
    set "bak_path=%%~dpa"
    if not exist "!bak_path!" mkdir "!bak_path!"
)

:: 根据模式处理
if "!mode!"=="ADD" (
    if not exist "!target_file!" (
        echo   - 模式: 新增文件

        :: 确保目标目录存在
        for %%a in ("!target_file!") do (
            set "target_dir=%%~dpa"
            if not exist "!target_dir!" mkdir "!target_dir!"
        )

        :: 创建一个1字节的备份文件表示这是ADD模式
        echo. > "!bak_file!"
        copy "!source_file!" "!target_file!" >nul
        echo   √ 新增文件: !target_file!
        exit /b 0
    ) else (
        echo   X 文件已存在(跳过): !target_file!
        exit /b 1
    )
)

:: 其他模式需要目标文件存在
if not exist "!target_file!" (
    echo   X 目标文件不存在: !target_file!
    exit /b 2
)

:: 创建备份(如果不存在)
if not exist "!bak_file!" (
    copy "!target_file!" "!bak_file!" >nul
    echo   + 创建备份: !bak_file!
)

:: 根据不同模式执行操作
if "!mode!"=="REPLACE" (
    echo   - 模式: 完全替换
    copy "!source_file!" "!target_file!" >nul
    echo   √ 完全替换: !target_file!

) else if "!mode!"=="REPLACE0" (
    echo   - 模式: 替换标记行
    "%~dp0sed.exe" -i "/!val1!/c\\$(type "!source_file!")" "!target_file!"
    echo   √ 替换标记行: !val1!

) else if "!mode!"=="REPLACE1" (
    echo   - 模式: 替换标记间内容
    "%~dp0sed.exe" -e "/!val1!/,/!val2!/ { /!val1!/p; /!val1!/r !source_file!; /!val1!/,/!val2!/d; /!val2!/p; }" -i "!target_file!"
    echo   √ 替换内容: [!val1!]到[!val2!]之间

) else if "!mode!"=="APPEND" (
    echo   - 模式: 追加到文件末尾
    if "!val1!"=="" (
        type "!source_file!" >> "!target_file!"
        echo   √ 追加到文件末尾
    ) else (
        :: val1表示倒数第几行
        for /f %%i in ('find /c /v "" ^<"!target_file!"') do set totallines=%%i
        set /a insertline=totallines-val1
        if !insertline! lss 0 set insertline=0
        "%~dp0sed.exe" -i "!insertline!r !source_file!" "!target_file!"
        echo   √ 追加到倒数第!val1!行
    )

) else if "!mode!"=="INSERT" (
    echo   - 模式: 在标记后插入
    "%~dp0sed.exe" -i "/!val1!/r !source_file!" "!target_file!"
    echo   √ 在[!val1!]后插入内容

) else (
    echo   X 未知模式: !mode!
    exit /b 3
)

exit /b 0
