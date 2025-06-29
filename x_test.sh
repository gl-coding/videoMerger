#!/bin/bash

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <文本文件路径> [搜索关键词] [输出文件夹]"
    echo "示例: $0 3866031f-9ba5-486f-8753-a1587a0b7821.txt"
    echo "示例: $0 3866031f-9ba5-486f-8753-a1587a0b7821.txt 1440w"
    echo "示例: $0 3866031f-9ba5-486f-8753-a1587a0b7821.txt 1440w my_images"
    exit 1
fi

# 获取参数
input_file="$1"
search_keyword="${2:-1440w}"  # 默认搜索关键词为1440w
output_folder="${3:-downloaded_images}"  # 默认输出文件夹为downloaded_images

# 检查文件是否存在
if [ ! -f "$input_file" ]; then
    echo "错误: 文件 '$input_file' 不存在"
    exit 1
fi

echo "输入文件: $input_file"
echo "搜索关键词: $search_keyword"
echo "输出文件夹: $output_folder"

# 获取所有图片链接（排除包含"链接"的行）
echo "正在搜索图片链接..."
urls=$(grep "$search_keyword" "$input_file" | grep -v 链接)

# 检查是否找到链接
if [ -z "$urls" ]; then
    echo "未找到任何图片链接"
    exit 1
fi

# 创建下载目录
mkdir -p "$output_folder"
cd "$output_folder"

# 计数器
count=0
total=$(echo "$urls" | wc -l)

echo "找到 $total 个图片链接，开始下载..."

# 逐个下载图片
echo "$urls" | while IFS= read -r url; do
    if [ -n "$url" ]; then
        count=$((count + 1))
        
        # 按照序号命名文件，统一格式：001.jpg, 002.jpg, ...
        filename=$(printf "%03d.jpg" $count)
        
        echo "[$count/$total] 下载: $filename"
        echo "URL: $url"
        
        # 使用curl下载，如果失败则尝试wget
        if command -v curl >/dev/null 2>&1; then
            curl -L -o "$filename" "$url" --connect-timeout 30 --max-time 60
        elif command -v wget >/dev/null 2>&1; then
            wget -O "$filename" "$url" --timeout=60
        else
            echo "错误: 未找到 curl 或 wget 命令"
            exit 1
        fi
        
        # 检查下载是否成功
        if [ -f "$filename" ] && [ -s "$filename" ]; then
            echo "✓ 下载成功: $filename"
        else
            echo "✗ 下载失败: $filename"
            rm -f "$filename" 2>/dev/null
        fi
        
        echo "---"
        
        # 添加小延迟避免请求过快
        sleep 1
    fi
done

echo "下载完成！"
echo "图片保存在: $(pwd)"
ls -la *.jpg 2>/dev/null | wc -l | xargs echo "成功下载图片数量:"
