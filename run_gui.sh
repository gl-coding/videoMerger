#!/bin/bash

# 文本输入GUI程序启动脚本

echo "正在启动文本输入GUI程序..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查是否安装了PyQt5
python3 -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "警告: 未找到PyQt5，正在尝试安装..."
    pip3 install PyQt5==5.15.10
    if [ $? -ne 0 ]; then
        echo "错误: PyQt5安装失败，请手动安装: pip3 install PyQt5"
        exit 1
    fi
fi

# 运行GUI程序
python3 text_input_gui.py

echo "程序已退出" 