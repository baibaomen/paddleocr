@echo off
setlocal

:: 设置虚拟环境名称
set VENV_NAME=venv

:: 检查python是否安装
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 需要安装 Python
    exit /b 1
)

:: 检查虚拟环境是否存在
if not exist %VENV_NAME%\Scripts\activate.bat (
    echo 创建虚拟环境...
    python -m venv %VENV_NAME%
    if %ERRORLEVEL% neq 0 (
        echo 创建虚拟环境失败
        exit /b 1
    )
)

:: 激活虚拟环境
echo 激活虚拟环境...
call %VENV_NAME%\Scripts\activate.bat

:: 升级pip
echo 升级pip...
python -m pip install --upgrade pip

:: 安装依赖
echo 安装依赖...
pip install -r requirements.txt

:: 启动应用
echo 启动应用...
python app.py

endlocal 