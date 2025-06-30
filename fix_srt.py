#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版字幕纠错工具 - 处理数字转换问题
"""

import re
import os
import argparse
import sys

def preprocess_text_for_alignment(text):
    """预处理文本，标准化数字格式以便对齐"""
    # 数字标准化映射
    replacements = {
        '三千': '3000',
        '两千五': '2500',
        '一千': '1000',
        '二千': '2000',
        '四千': '4000',
        '五千': '5000',
    }
    
    for cn_num, ar_num in replacements.items():
        text = text.replace(cn_num, ar_num)
    
    return text

def remove_punctuation_and_spaces(text):
    """移除文本中的标点符号和空格"""
    punctuation = '！？。，、；：""''（）【】《》〈〉…—–-·～!?.,;:"\'()[]<>~`@#$%^&*+=|\\/'
    for p in punctuation:
        text = text.replace(p, '')
    text = re.sub(r'\s+', '', text)
    return text

def parse_srt(srt_path):
    """解析SRT文件"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = re.split(r'\n\n+', content.strip())
    subtitles = []
    
    for block in blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        try:
            number = int(lines[0])
            timestamp = lines[1]
            text = ' '.join(lines[2:])
            
            subtitles.append({
                'number': number,
                'timestamp': timestamp,
                'text': text
            })
        except (ValueError, IndexError):
            continue
    
    return subtitles

def correct_subtitles_with_mapping(original_text_path, srt_path, output_path):
    """使用字符映射纠正字幕"""
    
    # 读取原始文本
    with open(original_text_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    # 解析SRT文件
    subtitles = parse_srt(srt_path)
    
    # 预处理：标准化数字格式
    original_normalized = preprocess_text_for_alignment(original_text)
    
    # 移除标点符号
    clean_original = remove_punctuation_and_spaces(original_normalized)
    
    print(f"原始文本长度：{len(clean_original)} 字符")
    print(f"解析到 {len(subtitles)} 条字幕")
    
    # 处理字幕文本
    all_subtitle_texts = []
    total_subtitle_length = 0
    
    for subtitle in subtitles:
        # 标准化字幕中的数字
        normalized_subtitle = preprocess_text_for_alignment(subtitle['text'])
        clean_subtitle = remove_punctuation_and_spaces(normalized_subtitle)
        all_subtitle_texts.append(clean_subtitle)
        total_subtitle_length += len(clean_subtitle)
    
    print(f"字幕文本总长度：{total_subtitle_length} 字符")
    
    # 如果长度匹配，进行逐字替换
    if abs(len(clean_original) - total_subtitle_length) <= 5:  # 允许小幅差异
        print("长度基本匹配，执行逐字替换...")
        corrected_subtitles = []
        original_index = 0
        
        for i, subtitle in enumerate(subtitles):
            subtitle_length = len(all_subtitle_texts[i])
            
            if original_index + subtitle_length <= len(clean_original):
                corrected_text = clean_original[original_index:original_index + subtitle_length]
                original_index += subtitle_length
            else:
                corrected_text = clean_original[original_index:] if original_index < len(clean_original) else all_subtitle_texts[i]
                original_index = len(clean_original)
            
            corrected_subtitles.append({
                'number': subtitle['number'],
                'timestamp': subtitle['timestamp'],
                'text': corrected_text,
                'original': subtitle['text']
            })
    else:
        print(f"长度差异过大 ({abs(len(clean_original) - total_subtitle_length)} 字符)，使用智能匹配...")
        # 使用更复杂的匹配算法
        corrected_subtitles = smart_align_and_correct(clean_original, subtitles, all_subtitle_texts)
    
    # 写入纠正后的SRT文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for subtitle in corrected_subtitles:
            f.write(f"{subtitle['number']}\n")
            f.write(f"{subtitle['timestamp']}\n")
            f.write(f"{subtitle['text']}\n\n")
    
    return corrected_subtitles

def smart_align_and_correct(clean_original, subtitles, all_subtitle_texts):
    """智能对齐和纠正"""
    corrected_subtitles = []
    
    # 将所有字幕文本连接
    combined_subtitle = ''.join(all_subtitle_texts)
    
    # 寻找最佳匹配起始位置
    best_match_score = 0
    best_start_pos = 0
    window_size = min(50, len(combined_subtitle))
    
    for start_pos in range(max(0, len(clean_original) - len(combined_subtitle) - 10), 
                           min(len(clean_original), 10)):
        if start_pos + window_size <= len(clean_original):
            original_window = clean_original[start_pos:start_pos + window_size]
            subtitle_window = combined_subtitle[:window_size]
            
            # 计算匹配分数
            match_score = sum(1 for i in range(window_size) if original_window[i] == subtitle_window[i])
            
            if match_score > best_match_score:
                best_match_score = match_score
                best_start_pos = start_pos
    
    print(f"最佳匹配起始位置：{best_start_pos}，匹配分数：{best_match_score}/{window_size}")
    
    # 从最佳位置开始逐字替换
    original_index = best_start_pos
    
    for i, subtitle in enumerate(subtitles):
        subtitle_length = len(all_subtitle_texts[i])
        
        if original_index + subtitle_length <= len(clean_original):
            corrected_text = clean_original[original_index:original_index + subtitle_length]
            original_index += subtitle_length
        else:
            # 如果超出范围，使用原文本
            corrected_text = all_subtitle_texts[i]
        
        corrected_subtitles.append({
            'number': subtitle['number'],
            'timestamp': subtitle['timestamp'],
            'text': corrected_text,
            'original': subtitle['text']
        })
    
    return corrected_subtitles

def main():
    parser = argparse.ArgumentParser(description='字幕纠错工具 - 使用原始文本纠正SRT字幕文件中的错误')
    parser.add_argument('original_text', help='原始文本文件路径')
    parser.add_argument('srt_file', help='需要纠正的SRT字幕文件路径')
    parser.add_argument('-o', '--output', help='输出的纠正后SRT文件路径（默认在原SRT文件目录生成）')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细对比信息')
    parser.add_argument('--show-all', action='store_true', help='显示所有字幕对比（默认只显示前10条）')
    
    args = parser.parse_args()
    
    # 设置输出文件路径
    if args.output:
        output_file = args.output
    else:
        # 默认在原SRT文件目录生成，文件名加上_corrected后缀
        srt_dir = os.path.dirname(args.srt_file)
        srt_name = os.path.splitext(os.path.basename(args.srt_file))[0]
        output_file = os.path.join(srt_dir, f"{srt_name}_corrected.srt")
    
    # 检查文件是否存在
    if not os.path.exists(args.original_text):
        print(f"错误：原始文本文件不存在：{args.original_text}")
        sys.exit(1)
    
    if not os.path.exists(args.srt_file):
        print(f"错误：SRT字幕文件不存在：{args.srt_file}")
        sys.exit(1)
    
    print("开始纠正字幕文件（处理数字对齐）...")
    print(f"原始文本：{args.original_text}")
    print(f"SRT文件：{args.srt_file}")
    print(f"输出文件：{output_file}")
    
    # 执行纠错
    corrected_subtitles = correct_subtitles_with_mapping(args.original_text, args.srt_file, output_file)
    
    print(f"\n纠错完成！输出文件：{output_file}")
    
    # 显示对比信息
    if args.verbose:
        print("\n=== 纠错对比 ===")
        show_count = len(corrected_subtitles) if args.show_all else 10
        
        for i, subtitle in enumerate(corrected_subtitles[:show_count]):
            original_clean = remove_punctuation_and_spaces(preprocess_text_for_alignment(subtitle['original']))
            corrected_clean = remove_punctuation_and_spaces(subtitle['text'])
            
            if original_clean != corrected_clean:
                print(f"\n第{i+1}条 [{subtitle['timestamp']}] - 已纠正:")
                print(f"  原始：{subtitle['original']}")
                print(f"  纠正：{subtitle['text']}")
            else:
                print(f"\n第{i+1}条 [{subtitle['timestamp']}] - 无需纠正:")
                print(f"  文本：{subtitle['text']}")
        
        if not args.show_all and len(corrected_subtitles) > 10:
            print(f"\n... 还有 {len(corrected_subtitles) - 10} 条字幕，使用 --show-all 查看全部")
    
    # 显示统计信息
    corrected_count = 0
    for subtitle in corrected_subtitles:
        original_clean = remove_punctuation_and_spaces(preprocess_text_for_alignment(subtitle['original']))
        corrected_clean = remove_punctuation_and_spaces(subtitle['text'])
        if original_clean != corrected_clean:
            corrected_count += 1
    
    print(f"\n=== 统计信息 ===")
    print(f"总字幕条数：{len(corrected_subtitles)}")
    print(f"纠正条数：{corrected_count}")
    print(f"无需纠正：{len(corrected_subtitles) - corrected_count}")
    print(f"纠正率：{corrected_count/len(corrected_subtitles)*100:.1f}%")

if __name__ == "__main__":
    main()