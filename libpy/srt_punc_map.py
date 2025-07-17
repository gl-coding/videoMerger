#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import argparse
import difflib

def add_punctuation(content_file, srt_words_file, output_file):
    """
    将content.txt中的标点符号添加到content_srt_words.txt中，并生成新文件
    
    Args:
        content_file: 包含原始文本的文件路径
        srt_words_file: 包含字幕时间轴的文件路径
        output_file: 输出文件路径
    """
    # 读取content文件内容
    with open(content_file, 'r', encoding='utf-8') as f:
        content_text = f.read().strip()
    
    # 读取srt_words文件内容
    with open(srt_words_file, 'r', encoding='utf-8') as f:
        srt_words_lines = f.readlines()
    
    # 提取所有标点符号及其位置
    punctuation_pattern = r'[，。；：？！、""''（）【】《》…—,.!?:;\'"()]'
    
    # 从字幕文件中提取纯文本（不包含标点）
    srt_text = ""
    srt_char_to_line = {}  # 字符在纯文本中的位置 -> 行号的映射
    line_index = 0
    
    # 首先清理字幕文件中可能存在的标点符号
    cleaned_lines = []
    for line in srt_words_lines:
        match = re.search(r'(\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+)\s+(.+)$', line)
        if match:
            time_part = match.group(1)
            text_part = match.group(2).strip()
            # 去除可能存在的标点符号
            clean_text = re.sub(punctuation_pattern, '', text_part)
            if clean_text:  # 确保不是空字符或只有标点
                cleaned_lines.append(f"{time_part}  {clean_text}\n")
            else:
                cleaned_lines.append(line)  # 如果清理后为空，保留原行
        else:
            cleaned_lines.append(line)  # 如果不匹配格式，保留原行
    
    # 从清理后的字幕文件中构建字符映射
    for line in cleaned_lines:
        match = re.search(r'\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+\s+(.+)$', line)
        if match:
            char = match.group(1).strip()
            if char:  # 确保不是空字符
                srt_text += char
                # 记录该字符在纯文本中的位置对应的行号
                srt_char_to_line[len(srt_text) - 1] = line_index
        line_index += 1
    
    # 从原始内容中提取纯文本（不包含标点）
    content_clean = re.sub(punctuation_pattern, '', content_text)
    
    # 使用序列匹配找到两个文本之间的对应关系
    matcher = difflib.SequenceMatcher(None, content_clean, srt_text)
    
    # 创建一个映射：原文中的字符位置 -> 字幕文件中的字符位置
    content_to_srt_pos = {}
    
    for block in matcher.get_matching_blocks():
        content_start, srt_start, size = block
        for i in range(size):
            content_to_srt_pos[content_start + i] = srt_start + i
    
    # 找出原文中所有的标点符号
    punctuations = []
    for match in re.finditer(punctuation_pattern, content_text):
        punctuations.append((match.start(), match.group()))
    
    # 复制清理后的行
    result_lines = cleaned_lines.copy()
    
    # 为每个标点符号找到应该插入的位置
    for pos, punct in punctuations:
        # 找到标点前面的字符在原文中的位置
        prev_char_pos = pos - 1
        while prev_char_pos >= 0 and re.match(punctuation_pattern, content_text[prev_char_pos]):
            prev_char_pos -= 1
        
        if prev_char_pos < 0:
            # 如果标点在文本开头，尝试找到第一个非标点字符
            next_char_pos = pos + 1
            while next_char_pos < len(content_text) and re.match(punctuation_pattern, content_text[next_char_pos]):
                next_char_pos += 1
            
            if next_char_pos < len(content_text):
                # 找到标点后面的字符在字幕中的位置
                content_char_pos = next_char_pos - len(re.findall(punctuation_pattern, content_text[:next_char_pos]))
                if content_char_pos in content_to_srt_pos:
                    srt_pos = content_to_srt_pos[content_char_pos]
                    if srt_pos in srt_char_to_line:
                        line_idx = srt_char_to_line[srt_pos]
                        # 在该行前面添加标点
                        line = result_lines[line_idx]
                        parts = line.split("  ", 1)
                        if len(parts) == 2:
                            time_part, text_part = parts
                            result_lines[line_idx] = f"{time_part}  {punct}{text_part}"
            continue
        
        # 计算标点前面的字符在原文纯文本中的位置（去除之前的标点）
        content_char_pos = prev_char_pos - len(re.findall(punctuation_pattern, content_text[:prev_char_pos+1]))
        
        # 找到对应的字幕位置
        if content_char_pos in content_to_srt_pos:
            srt_pos = content_to_srt_pos[content_char_pos]
            if srt_pos in srt_char_to_line:
                line_idx = srt_char_to_line[srt_pos]
                # 在该行后面添加标点
                line = result_lines[line_idx]
                parts = line.split("  ", 1)
                if len(parts) == 2:
                    time_part, text_part = parts
                    # 确保不会有重复的标点
                    if not text_part.strip().endswith(punct):
                        result_lines[line_idx] = f"{time_part}  {text_part.strip()}{punct}\n"
    
    # 写入新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)
    
    print(f"已生成带标点的字幕文件: {output_file}")
    
    # 生成对比文件
    comparison_file = output_file.replace('.txt', '_comparison.txt')
    generate_comparison(content_file, output_file, comparison_file)
    print(f"已生成对比文件: {comparison_file}")

def generate_comparison(content_file, output_file, comparison_file):
    """
    生成对比文件，包含原文和处理后的字幕文本
    """
    # 读取原文
    with open(content_file, 'r', encoding='utf-8') as f:
        content_text = f.read().strip()
    
    # 从处理后的字幕文件中提取文本
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    subtitle_text = ""
    for line in lines:
        match = re.search(r'\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+\s+(.+)$', line)
        if match:
            subtitle_text += match.group(1).strip()
    
    # 写入对比文件
    with open(comparison_file, 'w', encoding='utf-8') as f:
        f.write("=== 原文内容 ===\n\n")
        f.write(content_text)
        f.write("\n\n=== 字幕文本 ===\n\n")
        f.write(subtitle_text)
        f.write("\n\n=== 字符级对比 ===\n\n")
        
        # 逐字符对比
        punct_pattern = r'[，。；：？！、""''（）【】《》…—,.!?:;\'"()]'
        content_clean = re.sub(punct_pattern, '', content_text)
        subtitle_clean = re.sub(punct_pattern, '', subtitle_text)
        
        f.write(f"原文字符数（不含标点）: {len(content_clean)}\n")
        f.write(f"字幕字符数（不含标点）: {len(subtitle_clean)}\n\n")
        
        # 使用difflib比较差异
        d = difflib.Differ()
        diff = list(d.compare(content_clean, subtitle_clean))
        f.write("差异对比：\n")
        f.write(''.join(diff))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='将原始文本中的标点符号添加到字幕时间轴文件中')
    parser.add_argument('content_file', help='包含原始文本的文件路径')
    parser.add_argument('srt_words_file', help='包含字幕时间轴的文件路径')
    parser.add_argument('output_file', help='输出文件路径')
    
    args = parser.parse_args()
    
    add_punctuation(args.content_file, args.srt_words_file, args.output_file)
    print(f"处理完成!") 