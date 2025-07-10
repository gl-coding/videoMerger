#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕纠错工具 - 基于字符映射和句子映射的纠错算法
"""

import re
import os
import argparse
import sys
import difflib

def clean_text_for_comparison(text):
    """清理文本用于比较，移除标点和空格但保留内容"""
    punctuation = '！？。，、；：""''（）【】《》〈〉…—–-·～!?.,;:"\'()[]<>~`@#$%^&*+=|\\/'
    cleaned = text
    for p in punctuation:
        cleaned = cleaned.replace(p, '')
    cleaned = re.sub(r'\s+', '', cleaned)
    return cleaned

def get_char_count_diff(text1, text2):
    """计算两个文本的字符数差值（排除标点符号）"""
    clean_text1 = clean_text_for_comparison(text1)
    clean_text2 = clean_text_for_comparison(text2)
    return len(clean_text2) - len(clean_text1)

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
            number = int(lines[0].strip())
            timestamp = lines[1].strip()
            text_lines = [line.strip() for line in lines[2:]]
            text = ' '.join(text_lines)
            
            subtitles.append({
                'number': number,
                'timestamp': timestamp,
                'text': text
            })
        except (ValueError, IndexError):
            continue
    
    return subtitles

def get_combined_segments(segments, position, max_combine=3):
    """获取不同组合的前后句拼接结果"""
    combinations = []
    n = len(segments)
    idx = position - 1  # 转换为0基索引
    
    # 获取基准文本
    base_text = segments[idx]
    combinations.append(('base', base_text))
    
    # 向前拼接1-3句
    for i in range(1, max_combine + 1):
        start = max(0, idx - i)
        combined = ''.join(segments[start:idx + 1])
        combinations.append((f'prev_{i}', combined))
    
    # 向后拼接1-3句
    for i in range(1, max_combine + 1):
        end = min(n, idx + 1 + i)
        combined = ''.join(segments[idx:end])
        combinations.append((f'next_{i}', combined))
    
    # 前后同时拼接
    for i in range(1, max_combine + 1):
        for j in range(1, max_combine + 1):
            start = max(0, idx - i)
            end = min(n, idx + 1 + j)
            combined = ''.join(segments[start:end])
            combinations.append((f'both_{i}_{j}', combined))
    
    return combinations

def find_best_match(subtitle_text, segment_info):
    """找到最佳匹配的原文片段"""
    clean_subtitle = clean_text_for_comparison(subtitle_text)
    best_match = None
    best_similarity = -1
    best_sentence = None
    best_position = None
    best_segments = None
    best_combine_type = 'base'
    best_char_diff = 0
    
    for segment, info in segment_info.items():
        clean_segment = clean_text_for_comparison(segment)
        if not clean_segment:
            continue
        
        # 计算基本相似度
        similarity = difflib.SequenceMatcher(None, clean_subtitle, clean_segment).ratio()
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = segment
            best_sentence = info['sentence']
            best_position = info['position']
            best_segments = info['all_segments']
            best_char_diff = get_char_count_diff(subtitle_text, segment)
            
            # 尝试不同的拼接组合
            segments_list = info['all_segments'].split('|')
            combinations = get_combined_segments(segments_list, info['position'])
            
            for combine_type, combined_text in combinations:
                clean_combined = clean_text_for_comparison(combined_text)
                combined_similarity = difflib.SequenceMatcher(None, clean_subtitle, clean_combined).ratio()
                
                # 如果拼接后的相似度更高（设置一个小的阈值避免微小的改进）
                if combined_similarity > best_similarity + 0.05:
                    best_similarity = combined_similarity
                    best_match = combined_text
                    best_combine_type = combine_type
                    best_char_diff = get_char_count_diff(subtitle_text, combined_text)
    
    return best_match, best_similarity, best_sentence, best_position, best_segments, best_combine_type, best_char_diff

def split_sentence_to_segments(sentence, segment_delimiters):
    """将长句分割为短句列表"""
    segments = re.split(f'({segment_delimiters})', sentence)
    processed_segments = []
    i = 0
    while i < len(segments):
        if i + 1 < len(segments) and re.match(segment_delimiters, segments[i+1]):
            segment = (segments[i] + segments[i+1]).strip()
            if segment:
                processed_segments.append(segment)
            i += 2
        else:
            if segments[i].strip():
                processed_segments.append(segments[i].strip())
            i += 1
    return processed_segments

def generate_sentence_mapping(original_text_path, srt_path, output_path, corrected_srt_path=None):
    """生成字幕文件语句和原文语句的映射文件，并可选择同时更正字幕"""
    with open(original_text_path, 'r', encoding='utf-8') as f:
        original_text = f.read().strip()
    
    subtitles = parse_srt(srt_path)
    
    # 首先分割原文为长句
    sentence_delimiters = '[。！？!?]'
    sentences = re.split(f'({sentence_delimiters})', original_text)
    processed_sentences = []
    i = 0
    while i < len(sentences):
        if i + 1 < len(sentences) and re.match(sentence_delimiters, sentences[i+1]):
            processed_sentences.append((sentences[i] + sentences[i+1]).strip())
            i += 2
        else:
            if sentences[i].strip():
                processed_sentences.append(sentences[i].strip())
            i += 1
    
    # 然后分割每个长句为短句，并保持短句到长句的映射关系
    segment_delimiters = '[。，；：！？、,.;:!?"\'""''「」『』【】《》〈〉—–-…～]'
    segment_info = {}
    
    for sentence in processed_sentences:
        segments = split_sentence_to_segments(sentence, segment_delimiters)
        for idx, segment in enumerate(segments, 1):
            segment_info[segment] = {
                'sentence': sentence,
                'position': idx,
                'all_segments': '|'.join(segments)
            }
    
    # 处理每个字幕条目
    corrected_subtitles = []
    mappings = []
    
    for subtitle in subtitles:
        subtitle_text = subtitle['text'].strip()
        if not subtitle_text:
            continue
        
        best_match, similarity, original_sentence, position, segments, combine_type, char_diff = find_best_match(subtitle_text, segment_info)
        
        mappings.append({
            'subtitle_number': subtitle['number'],
            'subtitle_text': subtitle_text,
            'corrected_text': best_match,
            'similarity': similarity,
            'char_diff': char_diff,
            'original_sentence': original_sentence,
            'position': position,
            'segments': segments,
            'combine_type': combine_type
        })
        
        corrected_subtitles.append({
            'number': subtitle['number'],
            'timestamp': subtitle['timestamp'],
            'text': best_match if best_match else subtitle_text
        })
    
    # 写入详细映射文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("字幕行号\t字幕\t修正文本\t相似度\t字数差值\t原文长句\t短句位置\t长句分割\t拼接类型\n")
        for mapping in mappings:
            f.write(f"{mapping['subtitle_number']}\t{mapping['subtitle_text']}\t"
                   f"{mapping['corrected_text']}\t{mapping['similarity']:.3f}\t"
                   f"{mapping['char_diff']}\t{mapping['original_sentence']}\t"
                   f"{mapping['position']}\t{mapping['segments']}\t"
                   f"{mapping['combine_type']}\n")
    
    print(f"详细映射文件已生成：{output_path}")
    
    # 写入简化版映射文件
    simple_mapping_path = os.path.join(os.path.dirname(output_path), 
                                     os.path.splitext(os.path.basename(output_path))[0] + "_simple.txt")
    with open(simple_mapping_path, 'w', encoding='utf-8') as f:
        f.write("字幕行号\t字幕\t修正文本\n")
        for mapping in mappings:
            f.write(f"{mapping['subtitle_number']}\t{mapping['subtitle_text']}\t"
                   f"{mapping['corrected_text']}\n")
    
    print(f"简化版映射文件已生成：{simple_mapping_path}")
    
    # 生成更正后的字幕文件
    if corrected_srt_path:
        with open(corrected_srt_path, 'w', encoding='utf-8') as f:
            for subtitle in corrected_subtitles:
                f.write(f"{subtitle['number']}\n")
                f.write(f"{subtitle['timestamp']}\n")
                f.write(f"{subtitle['text']}\n\n")
        
        print(f"更正后的字幕文件已生成：{corrected_srt_path}")
    
    return mappings

def main():
    parser = argparse.ArgumentParser(description='字幕纠错工具 - 基于句子映射的纠错算法')
    parser.add_argument('srt_file', help='需要纠正的SRT字幕文件路径')
    parser.add_argument('original_text', help='原始文本文件路径')
    parser.add_argument('-o', '--output', help='输出的纠正后SRT文件路径（默认在原SRT文件目录生成）')
    
    args = parser.parse_args()
    
    if args.output:
        output_file = args.output
    else:
        srt_dir = os.path.dirname(args.srt_file)
        srt_name = os.path.splitext(os.path.basename(args.srt_file))[0]
        output_file = os.path.join(srt_dir, f"{srt_name}_corrected.srt")
    
    if not os.path.exists(args.srt_file):
        print(f"错误：SRT字幕文件不存在：{args.srt_file}")
        sys.exit(1)
    
    if not os.path.exists(args.original_text):
        print(f"错误：原始文本文件不存在：{args.original_text}")
        sys.exit(1)
    
    srt_dir = os.path.dirname(args.srt_file)
    srt_name = os.path.splitext(os.path.basename(args.srt_file))[0]
    mapping_file = os.path.join(srt_dir, f"{srt_name}_mapping.txt")
    
    generate_sentence_mapping(args.original_text, args.srt_file, mapping_file, output_file)

if __name__ == "__main__":
    main()