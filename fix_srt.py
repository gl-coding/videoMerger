#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能字幕纠错工具 - 基于句子匹配的纠错算法
"""

import re
import os
import argparse
import sys
from difflib import SequenceMatcher

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

def split_text_into_sentences(text):
    """将文本分割成句子"""
    # 使用中文句号、问号、感叹号作为分句标准
    sentences = re.split(r'[。！？]', text)
    # 过滤空句子并添加回句号
    result = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            result.append(sentence)
    return result

def find_best_match(subtitle_text, original_sentences, used_sentences):
    """为字幕文本找到最佳匹配的原始句子"""
    subtitle_clean = clean_text_for_comparison(subtitle_text)
    best_score = 0
    best_match = None
    best_index = -1
    
    for i, orig_sentence in enumerate(original_sentences):
        if i in used_sentences:
            continue
            
        orig_clean = clean_text_for_comparison(orig_sentence)
        
        # 计算相似度
        similarity = SequenceMatcher(None, subtitle_clean, orig_clean).ratio()
        
        # 如果字幕文本是原始句子的子串，提高分数
        if subtitle_clean in orig_clean or orig_clean in subtitle_clean:
            similarity += 0.3
        
        # 长度相近的句子优先
        length_ratio = min(len(subtitle_clean), len(orig_clean)) / max(len(subtitle_clean), len(orig_clean), 1)
        similarity *= (0.5 + 0.5 * length_ratio)
        
        if similarity > best_score:
            best_score = similarity
            best_match = orig_sentence
            best_index = i
    
    return best_match, best_index, best_score

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

def correct_subtitles_intelligent(original_text_path, srt_path, output_path):
    """使用智能句子匹配纠正字幕"""
    
    # 读取原始文本
    with open(original_text_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    # 解析SRT文件
    subtitles = parse_srt(srt_path)
    
    # 预处理原始文本
    original_normalized = preprocess_text(original_text)
    
    # 将原始文本分割成句子
    original_sentences = split_text_into_sentences(original_normalized)
    
    print(f"原始文本分割成 {len(original_sentences)} 个句子")
    print(f"解析到 {len(subtitles)} 条字幕")
    
    # 纠正字幕
    corrected_subtitles = []
    used_sentences = set()
    
    for subtitle in subtitles:
        # 预处理字幕文本
        subtitle_normalized = preprocess_text(subtitle['text'])
        
        # 寻找最佳匹配
        best_match, best_index, score = find_best_match(subtitle_normalized, original_sentences, used_sentences)
        
        if best_match and score > 0.3:  # 相似度阈值
            corrected_text = best_match
            used_sentences.add(best_index)
            print(f"字幕 {subtitle['number']}: 匹配度 {score:.3f}")
        else:
            # 如果没有好的匹配，保留原文但进行基本清理
            corrected_text = subtitle_normalized
            print(f"字幕 {subtitle['number']}: 无匹配，保留原文")
        
        corrected_subtitles.append({
            'number': subtitle['number'],
            'timestamp': subtitle['timestamp'], 
            'text': corrected_text,
            'original': subtitle['text']
        })
    
    # 处理未使用的句子（可能是长句子被拆分了）
    unused_sentences = [i for i in range(len(original_sentences)) if i not in used_sentences]
    if unused_sentences:
        print(f"有 {len(unused_sentences)} 个句子未匹配，可能需要手动检查")
    
    # 写入纠正后的SRT文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for subtitle in corrected_subtitles:
            f.write(f"{subtitle['number']}\n")
            f.write(f"{subtitle['timestamp']}\n")
            f.write(f"{subtitle['text']}\n\n")
    
    return corrected_subtitles

def main():
    parser = argparse.ArgumentParser(description='智能字幕纠错工具 - 基于句子匹配的纠错算法')
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
    
    print("开始智能纠正字幕文件...")
    print(f"原始文本：{args.original_text}")
    print(f"SRT文件：{args.srt_file}")
    print(f"输出文件：{output_file}")
    
    # 执行纠错
    corrected_subtitles = correct_subtitles_intelligent(args.original_text, args.srt_file, output_file)
    
    print(f"\n纠错完成！输出文件：{output_file}")
    
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
    
    # 显示统计信息
    corrected_count = sum(1 for subtitle in corrected_subtitles if subtitle['original'] != subtitle['text'])
    
    print(f"\n=== 统计信息 ===")
    print(f"总字幕条数：{len(corrected_subtitles)}")
    print(f"纠正条数：{corrected_count}")
    print(f"无需纠正：{len(corrected_subtitles) - corrected_count}")
    print(f"纠正率：{corrected_count/len(corrected_subtitles)*100:.1f}%")

if __name__ == "__main__":
    main()