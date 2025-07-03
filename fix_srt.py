#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕纠错工具 - 基于字符映射的纠错算法
"""

import re
import os
import argparse
import sys

def preprocess_text(text):
    """预处理文本，标准化但保留句子结构"""
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

def clean_text_for_comparison(text):
    """清理文本用于比较，移除标点和空格但保留内容"""
    # 移除标点符号和空格
    punctuation = '！？。，、；：""''（）【】《》〈〉…—–-·～!?.,;:"\'()[]<>~`@#$%^&*+=|\\/'
    cleaned = text
    for p in punctuation:
        cleaned = cleaned.replace(p, '')
    cleaned = re.sub(r'\s+', '', cleaned)
    return cleaned

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

def generate_character_mapping(original_text_path, srt_path, mapping_output_path):
    """生成字符级别的一对一映射文件"""
    
    # 读取原始文本
    with open(original_text_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    # 解析SRT文件
    subtitles = parse_srt(srt_path)
    
    # 预处理文本，移除标点和空格
    original_clean = clean_text_for_comparison(preprocess_text(original_text))
    
    # 合并所有字幕文本
    all_subtitle_text = ""
    for subtitle in subtitles:
        all_subtitle_text += subtitle['text']
    
    subtitle_clean = clean_text_for_comparison(preprocess_text(all_subtitle_text))
    
    print(f"原始文本长度：{len(original_clean)} 字符")
    print(f"字幕文本长度：{len(subtitle_clean)} 字符")
    print(f"原始文本前50字符：{original_clean[:50]}")
    print(f"字幕文本前50字符：{subtitle_clean[:50]}")
    
    # 创建字符映射
    mappings = []
    
    # 如果长度相等，先尝试直接映射，但要验证准确性
    if len(original_clean) == len(subtitle_clean):
        print("长度相等，检查直接映射的准确性...")
        
        # 计算直接映射的匹配率
        direct_matches = sum(1 for i in range(len(original_clean)) if original_clean[i] == subtitle_clean[i])
        match_rate = direct_matches / len(original_clean)
        
        print(f"直接映射匹配率: {match_rate:.1%} ({direct_matches}/{len(original_clean)})")
        
        if match_rate >= 0.7:  # 如果匹配率高于70%，使用直接映射
            print("匹配率较高，使用直接映射...")
            for i in range(len(original_clean)):
                mappings.append(f"{subtitle_clean[i]}\t{original_clean[i]}")
        else:
            print("匹配率较低，使用滑动窗口搜索...")
            mappings = create_sliding_window_mapping(original_clean, subtitle_clean)
    else:
        print(f"长度不等，使用滑动窗口搜索...")
        mappings = create_sliding_window_mapping(original_clean, subtitle_clean)
    
    # 保存映射文件
    with open(mapping_output_path, 'w', encoding='utf-8') as f:
        for mapping in mappings:
            f.write(mapping + '\n')
    
    print(f"字符映射文件已生成：{mapping_output_path}")
    print(f"总映射条数：{len(mappings)}")
    
    # 显示一些有差异的映射作为检查
    different_mappings = []
    for mapping in mappings[:50]:  # 只检查前50个
        parts = mapping.split('\t')
        if len(parts) == 2 and parts[0] != parts[1]:
            different_mappings.append(mapping)
    
    if different_mappings:
        print(f"前50个字符中发现 {len(different_mappings)} 个差异映射:")
        for i, diff in enumerate(different_mappings[:10]):  # 只显示前10个
            print(f"  {diff}")
        if len(different_mappings) > 10:
            print(f"  ... 还有 {len(different_mappings) - 10} 个差异")
    
    return mappings

def create_sliding_window_mapping(original_clean, subtitle_clean):
    """使用滑动窗口创建字符映射"""
    mappings = []
    
    # 使用多个窗口大小进行搜索
    window_sizes = [50, 100, 200]
    best_alignment = None
    best_score = 0
    
    for window_size in window_sizes:
        window_size = min(window_size, len(subtitle_clean), len(original_clean))
        if window_size < 10:  # 窗口太小跳过
            continue
            
        print(f"尝试窗口大小: {window_size}")
        
        best_pos = 0
        best_window_score = 0
        
        # 搜索最佳起始位置
        max_search = len(original_clean) - window_size + 1
        for start_pos in range(min(max_search, 100)):  # 限制搜索范围避免过慢
            score = 0
            for i in range(window_size):
                if i < len(subtitle_clean) and start_pos + i < len(original_clean):
                    if original_clean[start_pos + i] == subtitle_clean[i]:
                        score += 1
            
            if score > best_window_score:
                best_window_score = score
                best_pos = start_pos
        
        window_match_rate = best_window_score / window_size
        print(f"  最佳位置: {best_pos}, 匹配率: {window_match_rate:.1%}")
        
        if window_match_rate > best_score:
            best_score = window_match_rate
            best_alignment = best_pos
    
    if best_alignment is not None:
        print(f"最终选择对齐位置: {best_alignment}, 匹配率: {best_score:.1%}")
        
        # 显示对齐示例
        if best_alignment + 20 <= len(original_clean) and 20 <= len(subtitle_clean):
            print("对齐示例:")
            print(f"原文: {original_clean[best_alignment:best_alignment+20]}")
            print(f"字幕: {subtitle_clean[:20]}")
    else:
        print("未找到合适的对齐位置，使用默认对齐")
        best_alignment = 0
    
    # 创建映射 - 优先考虑原文的完整性
    for i in range(len(original_clean)):
        subtitle_pos = i - best_alignment
        if 0 <= subtitle_pos < len(subtitle_clean):
            # 有对应的字幕字符
            mappings.append(f"{subtitle_clean[subtitle_pos]}\t{original_clean[i]}")
        else:
            # 没有对应的字幕字符，保持原文字符
            mappings.append(f"{original_clean[i]}\t{original_clean[i]}")
    
    return mappings

def load_character_mapping(mapping_file_path):
    """加载字符映射文件"""
    mapping_dict = {}
    
    with open(mapping_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '\t' in line:
                parts = line.split('\t')
                if len(parts) == 2:
                    wrong_char, correct_char = parts
                    mapping_dict[wrong_char] = correct_char
    
    print(f"加载了 {len(mapping_dict)} 个字符映射")
    return mapping_dict

def apply_character_mapping(text, mapping_dict):
    """根据字符映射纠正文本"""
    corrected_text = ""
    
    for char in text:
        # 如果字符在映射表中，使用映射后的字符
        if char in mapping_dict:
            corrected_text += mapping_dict[char]
        else:
            # 不在映射表中的字符保持原样（通常是标点符号）
            corrected_text += char
    
    return corrected_text

def correct_srt_with_mapping(original_text_path, srt_path, output_path):
    """使用字符映射文件纠正SRT字幕"""
    
    # 生成映射文件路径
    srt_dir = os.path.dirname(srt_path)
    srt_name = os.path.splitext(os.path.basename(srt_path))[0]
    mapping_file_path = os.path.join(srt_dir, f"{srt_name}_mapping.txt")
    
    # 先生成字符映射文件
    print("步骤1: 生成字符映射文件...")
    generate_character_mapping(original_text_path, srt_path, mapping_file_path)
    
    print("\n步骤2: 从映射文件提取正确的文本序列...")
    
    # 从映射文件中提取正确的字符序列
    correct_sequence = []
    with open(mapping_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '\t' in line:
                parts = line.split('\t')
                if len(parts) == 2:
                    wrong_char, correct_char = parts
                    correct_sequence.append(correct_char)
    
    print(f"提取到正确字符序列，长度: {len(correct_sequence)}")
    print(f"正确序列前50字符: {''.join(correct_sequence[:50])}")
    
    # 解析SRT文件
    subtitles = parse_srt(srt_path)
    print(f"解析到 {len(subtitles)} 条字幕")
    
    # 计算每条字幕对应的字符长度（去除标点符号）
    subtitle_char_lengths = []
    for subtitle in subtitles:
        # 预处理字幕文本，移除标点和空格
        clean_subtitle = clean_text_for_comparison(preprocess_text(subtitle['text']))
        subtitle_char_lengths.append(len(clean_subtitle))
    
    # 按字符长度重新分配正确的文本
    corrected_subtitles = []
    char_index = 0
    corrected_count = 0
    
    for i, subtitle in enumerate(subtitles):
        char_length = subtitle_char_lengths[i]
        
        if char_index + char_length <= len(correct_sequence):
            # 提取对应的正确字符
            correct_chars = correct_sequence[char_index:char_index + char_length]
            corrected_text = ''.join(correct_chars)
            char_index += char_length
        else:
            # 如果超出范围，使用剩余的所有字符
            remaining_chars = correct_sequence[char_index:]
            corrected_text = ''.join(remaining_chars)
            char_index = len(correct_sequence)
        
        # 恢复基本的标点符号
        corrected_text = restore_punctuation_from_original(corrected_text, subtitle['text'])
        
        # 检查是否有修改
        if corrected_text != subtitle['text']:
            corrected_count += 1
        
        corrected_subtitles.append({
            'number': subtitle['number'],
            'timestamp': subtitle['timestamp'],
            'text': corrected_text,
            'original': subtitle['text']
        })
    
    # 写入纠正后的SRT文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for subtitle in corrected_subtitles:
            f.write(f"{subtitle['number']}\n")
            f.write(f"{subtitle['timestamp']}\n")
            f.write(f"{subtitle['text']}\n\n")
    
    print(f"\n纠错完成！")
    print(f"映射文件：{mapping_file_path}")
    print(f"输出文件：{output_path}")
    print(f"总字幕条数：{len(corrected_subtitles)}")
    print(f"纠正条数：{corrected_count}")
    print(f"纠正率：{corrected_count/len(corrected_subtitles)*100:.1f}%")
    
    return corrected_subtitles

def restore_punctuation_from_original(corrected_text, original_subtitle_text):
    """根据原字幕的标点符号模式恢复纠正文本的标点"""
    if not corrected_text:
        return corrected_text
    
    # 获取原字幕的标点符号位置和类型
    punctuation = '！？。，、；：""''（）【】《》〈〉…—–-·～!?.,;:"\'()[]<>~`@#$%^&*+=|\\/'
    
    # 找出原字幕中的标点符号位置
    original_puncts = []
    original_chars = []
    for i, char in enumerate(original_subtitle_text):
        if char in punctuation:
            original_puncts.append((len(original_chars), char))  # (位置, 标点)
        elif not char.isspace():
            original_chars.append(char)
    
    # 构建带标点的纠正文本
    result = list(corrected_text)
    
    # 在相应位置插入标点符号
    for pos, punct in original_puncts:
        if pos <= len(result):
            result.insert(pos, punct)
    
    return ''.join(result)

def main():
    parser = argparse.ArgumentParser(description='字幕纠错工具 - 基于字符映射的纠错算法')
    parser.add_argument('original_text', help='原始文本文件路径')
    parser.add_argument('srt_file', help='需要纠正的SRT字幕文件路径')
    parser.add_argument('-o', '--output', help='输出的纠正后SRT文件路径（默认在原SRT文件目录生成）')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细对比信息')
    parser.add_argument('--show-all', action='store_true', help='显示所有字幕对比（默认只显示前10条）')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.original_text):
        print(f"错误：原始文本文件不存在：{args.original_text}")
        sys.exit(1)
    
    if not os.path.exists(args.srt_file):
        print(f"错误：SRT字幕文件不存在：{args.srt_file}")
        sys.exit(1)
    
    # 设置输出文件路径
    if args.output:
        output_file = args.output
    else:
        srt_dir = os.path.dirname(args.srt_file)
        srt_name = os.path.splitext(os.path.basename(args.srt_file))[0]
        output_file = os.path.join(srt_dir, f"{srt_name}_corrected.srt")
    
    print("开始字符映射纠错...")
    print(f"原始文本：{args.original_text}")
    print(f"SRT文件：{args.srt_file}")
    print(f"输出文件：{output_file}")
    
    # 执行纠错
    corrected_subtitles = correct_srt_with_mapping(args.original_text, args.srt_file, output_file)
    
    # 显示对比信息
    if args.verbose:
        print("\n=== 纠错对比 ===")
        show_count = len(corrected_subtitles) if args.show_all else 10
        
        for i, subtitle in enumerate(corrected_subtitles[:show_count]):
            if subtitle['original'] != subtitle['text']:
                print(f"\n第{i+1}条 [{subtitle['timestamp']}] - 已纠正:")
                print(f"  原始：{subtitle['original']}")
                print(f"  纠正：{subtitle['text']}")
            else:
                print(f"\n第{i+1}条 [{subtitle['timestamp']}] - 无需纠正:")
                print(f"  文本：{subtitle['text']}")
        
        if not args.show_all and len(corrected_subtitles) > 10:
            print(f"\n... 还有 {len(corrected_subtitles) - 10} 条字幕，使用 --show-all 查看全部")

if __name__ == "__main__":
    main()