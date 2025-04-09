@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

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
set "bak_dir=Sultan's Game_Data\StreamingAssets\config\bak"
if not exist "!bak_dir!" (
    mkdir "!bak_dir!"
)

:: 第二步：安装MOD - 正确的递归查找
echo [安装阶段] 开始处理MOD文件...
cd /d "%~dp0"

for /r "Mods" %%f in (*.json) do (
    set "json_file=%%f"
    set "config_file=%%~dpf%%~nf.json.config"
    call :handle_mod
)
goto :after_loop

:handle_mod
if exist "!config_file!" (
    echo [安装] !json_file!
    call :process_file "!json_file!" "!config_file!"
)
goto :eof

:after_loop


echo MOD安装完成！
pause
exit /b 0


:process_file
set "source_file=%~1"
set "config_file=%~2"

:: 读取配置文件
set /a line_num=0
for /f "usebackq delims=" %%a in ("!config_file!") do (
    set /a line_num+=1
    set "line_!line_num!=%%a"
)

set "mode=!line_1!"
set "target_file=Sultan's Game_Data\StreamingAssets\config\!line_2!"
set "val1=!line_3!"
set "val2=!line_4!"

:: 创建备份目录结构
set "bak_file=!bak_dir!\!line_2!.bak"
for %%a in ("!bak_file!") do (
    set "bak_path=%%~dpa"
    if not exist "!bak_path!" mkdir "!bak_path!"
)

:: ADD模式处理
if "!mode!"=="ADD" (
    if not exist "!target_file!" (
        echo. > "!bak_file!"
        copy "!source_file!" "!target_file!" >nul
        echo  √ 新增文件: !target_file!
    ) else (
        echo  X 文件已存在(跳过): !target_file!
    )
    goto :eof
)

:: 其他模式需要目标文件存在
if not exist "!target_file!" (
    echo  X 目标文件不存在: !target_file!
    goto :eof
)

:: 创建备份(如果不存在)
if not exist "!bak_file!" (
    copy "!target_file!" "!bak_file!" >nul
    echo  + 创建备份: !bak_file!
)

:: 根据模式处理
if "!mode!"=="REPLACE" (
    copy "!source_file!" "!target_file!" >nul
    echo  √ 完全替换: !target_file!
) else if "!mode!"=="REPLACE0" (
    "%~dp0sed.exe" -i "/!val1!/c\\^(type "!source_file!^")" "!target_file!"
    echo  √ 替换标记行: !val1!
) else if "!mode!"=="REPLACE1" (
    "%~dp0sed.exe" -e "/!val1!/,/!val2!/ { /!val1!/ { p; r "!source_file!" -e " }; /!val2!/p; d }" "!target_file!" > "!target_file!.tmp"
    move /y "!target_file!.tmp" "!target_file!" >nul
    echo  √ 替换内容: [!val1!]到[!val2!]之间
) else if "!mode!"=="APPEND" (
    type "!source_file!" >> "!target_file!"
    echo  √ 追加到文件末尾
) else if "!mode!"=="INSERT" (
    "%~dp0sed.exe" -i "/!val1!/ r "!source_file!"" "!target_file!"
    echo  √ 在[!val1!]后插入内容
) else (
    echo  X 未知模式: !mode!
)
goto :eof
