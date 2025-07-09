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

def find_best_match(subtitle_text, original_segments, segment_to_sentence):
    """找到最佳匹配的原文片段"""
    clean_subtitle = clean_text_for_comparison(subtitle_text)
    best_match = None
    best_similarity = -1
    best_sentence = None
    
    for segment, sentence in segment_to_sentence.items():
        clean_segment = clean_text_for_comparison(segment)
        if not clean_segment:
            continue
        
        similarity = difflib.SequenceMatcher(None, clean_subtitle, clean_segment).ratio()
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = segment
            best_sentence = sentence
    
    return best_match, best_similarity, best_sentence

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
    segment_to_sentence = {}
    
    for sentence in processed_sentences:
        segments = re.split(f'({segment_delimiters})', sentence)
        i = 0
        while i < len(segments):
            if i + 1 < len(segments) and re.match(segment_delimiters, segments[i+1]):
                segment = (segments[i] + segments[i+1]).strip()
                if segment:
                    segment_to_sentence[segment] = sentence
                i += 2
            else:
                if segments[i].strip():
                    segment_to_sentence[segments[i].strip()] = sentence
                i += 1
    
    # 处理每个字幕条目
    corrected_subtitles = []
    mappings = []
    
    for subtitle in subtitles:
        subtitle_text = subtitle['text'].strip()
        if not subtitle_text:
            continue
        
        best_match, similarity, original_sentence = find_best_match(subtitle_text, segment_to_sentence.keys(), segment_to_sentence)
        
        mappings.append({
            'subtitle_number': subtitle['number'],
            'subtitle_text': subtitle_text,
            'corrected_text': best_match,
            'original_sentence': original_sentence,
            'similarity': similarity
        })
        
        corrected_subtitles.append({
            'number': subtitle['number'],
            'timestamp': subtitle['timestamp'],
            'text': best_match if best_match else subtitle_text
        })
    
    # 写入映射文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("字幕行号\t字幕\t修正文本\t原文长句\t相似度\n")
        for mapping in mappings:
            f.write(f"{mapping['subtitle_number']}\t{mapping['subtitle_text']}\t"
                   f"{mapping['corrected_text']}\t{mapping['original_sentence']}\t"
                   f"{mapping['similarity']:.2f}\n")
    
    print(f"映射文件已生成：{output_path}")
    
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