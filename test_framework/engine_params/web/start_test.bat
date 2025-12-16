@echo off
REM C3DBaseline 测试运行器 - 快捷启动脚本
REM 双击此文件即可启动测试环境

echo.
echo ========================================
echo   C3DBaseline 测试运行器
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请确保 Python 已安装并添加到 PATH
    echo.
    pause
    exit /b 1
)

REM 显示 Python 版本
echo [信息] 使用 Python 版本:
python --version
echo.

REM 启动测试运行器
echo [启动] 正在启动测试运行器...
echo.
python start_test.py

REM 如果出错，保持窗口打开
if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请查看上面的错误信息
    echo.
    pause
)
