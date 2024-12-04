#!/bin/bash

# 设置虚拟环境名称
VENV_NAME="venv"

# 检查python3命令是否存在
if ! command -v python3 &> /dev/null; then
    echo "错误: 需要安装 Python 3"
    exit 1
fi

# 检查pip3命令是否存在
if ! command -v pip3 &> /dev/null; then
    echo "错误: 需要安装 pip3"
    exit 1
fi

# 检查虚拟环境是否已存在
if [ ! -d "$VENV_NAME" ]; then
    echo "创建虚拟环境..."
    python3 -m venv $VENV_NAME
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source $VENV_NAME/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 启动应用
echo "启动应用..."
python app.py 