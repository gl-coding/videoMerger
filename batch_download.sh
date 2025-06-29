#!/bin/bash

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法: $0 <目录路径> [搜索关键词] [输出文件夹前缀]"
    echo "示例: $0 dir"
    echo "示例: $0 dir 1440w"
    echo "示例: $0 dir 1440w doutu"
    echo "示例: $0 ~/Downloads 720w images"
    exit 1
fi

# 获取参数
target_dir="$1"
search_keyword="${2:-1440w}"  # 默认搜索关键词为1440w
folder_prefix="${3:-doutu}"   # 默认输出文件夹前缀为doutu

# 检查目录是否存在
if [ ! -d "$target_dir" ]; then
    echo "错误: 目录 '$target_dir' 不存在"
    exit 1
fi

# 检查x_test.sh是否存在
if [ ! -f "x_test.sh" ]; then
    echo "错误: x_test.sh 脚本不存在"
    exit 1
fi

# 确保x_test.sh有执行权限
chmod +x x_test.sh

echo "========================================="
echo "批量下载脚本启动"
echo "目标目录: $target_dir"
echo "搜索关键词: $search_keyword"
echo "输出文件夹前缀: $folder_prefix"
echo "========================================="

# 计数器
total_files=0
processed_files=0
success_count=0
error_count=0

# 统计总文件数
total_files=$(find "$target_dir" -type f -name "*.txt" | wc -l)
echo "找到 $total_files 个文本文件"

if [ $total_files -eq 0 ]; then
    echo "警告: 在目录 '$target_dir' 中未找到任何 .txt 文件"
    exit 0
fi

echo "开始处理..."
echo ""

# 遍历目录下的所有txt文件
find "$target_dir" -type f -name "*.txt" | while IFS= read -r file; do
    processed_files=$((processed_files + 1))
    
    # 获取文件名（不含路径和扩展名）
    filename=$(basename "$file" .txt)
    
    # 构造输出文件夹名
    output_folder="${folder_prefix}_${filename}"
    
    echo "[$processed_files/$total_files] 处理文件: $(basename "$file")"
    echo "输入文件: $file"
    echo "输出文件夹: $output_folder"
    
    # 执行下载命令
    if ./x_test.sh "$file" "$search_keyword" "$output_folder"; then
        echo "✓ 成功处理: $file"
        success_count=$((success_count + 1))
    else
        echo "✗ 处理失败: $file"
        error_count=$((error_count + 1))
    fi
    
    echo "----------------------------------------"
    echo ""
done

# 显示最终统计
echo "========================================="
echo "批量下载完成！"
echo "总文件数: $total_files"
echo "成功处理: $success_count"
echo "处理失败: $error_count"
echo "========================================="

# 显示生成的文件夹
echo "生成的文件夹:"
ls -la | grep "^d" | grep "$folder_prefix" | awk '{print $NF}' | head -10
if [ $(ls -la | grep "^d" | grep "$folder_prefix" | wc -l) -gt 10 ]; then
    echo "... 还有更多文件夹"
fi 