#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕纠错工具 - 基于字符映射的纠错算法
"""

import re
import os
import argparse
import sys
import difflib

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
            number = int(lines[0].strip())
            timestamp = lines[1].strip()  # 确保时间戳没有前后空格
            
            # 合并剩余的行作为字幕文本，确保没有多余的空格
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
    i = 0  # 原文索引
    j = 0  # 字幕索引
    while i < len(original_clean):
        if j >= len(subtitle_clean):
            # 字幕文本已结束，保持原文字符
            mappings.append(f"{original_clean[i]}\t{original_clean[i]}")
            i += 1
            continue
            
        # 向前看3个字符，检查是否存在连续匹配
        forward_match = 0
        for k in range(3):
            if (i + k < len(original_clean) and 
                j + k < len(subtitle_clean) and 
                original_clean[i + k] == subtitle_clean[j + k]):
                forward_match += 1
        
        if forward_match >= 2:
            # 如果前向匹配度高，说明当前对齐是正确的
            mappings.append(f"{subtitle_clean[j]}\t{original_clean[i]}")
            i += 1
            j += 1
        else:
            # 如果前向匹配度低，可能是字幕缺字，使用原文字符
            mappings.append(f"{original_clean[i]}\t{original_clean[i]}")
            i += 1
            # 不增加j，让字幕文本保持原位
            
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
    
    print("\n步骤2: 加载字符映射...")
    # 加载字符映射
    mapping_dict = {}
    with open(mapping_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '\t' in line:
                wrong_char, correct_char = line.split('\t')
                mapping_dict[wrong_char] = correct_char
    
    print(f"加载了 {len(mapping_dict)} 个字符映射")
    
    # 解析SRT文件
    subtitles = parse_srt(srt_path)
    print(f"解析到 {len(subtitles)} 条字幕")
    
    # 直接对每条字幕文本进行纠正
    corrected_subtitles = []
    corrected_count = 0
    
    for subtitle in subtitles:
        # 保留原始标点符号位置
        punctuation_positions = []
        text = subtitle['text']
        for i, char in enumerate(text):
            if not char.isalnum() and not char.isspace():
                punctuation_positions.append((i, char))
        
        # 清理文本，只保留字符
        clean_text = clean_text_for_comparison(text)
        
        # 纠正每个字符
        corrected_chars = []
        for char in clean_text:
            if char in mapping_dict:
                corrected_chars.append(mapping_dict[char])
            else:
                corrected_chars.append(char)
        
        # 重新插入标点符号
        for pos, punct in punctuation_positions:
            if pos < len(corrected_chars):
                corrected_chars.insert(pos, punct)
        
        corrected_text = ''.join(corrected_chars)
        
        # 检查是否有修改
        if corrected_text != subtitle['text']:
            corrected_count += 1
        
        corrected_subtitles.append({
            'number': subtitle['number'],
            'timestamp': subtitle['timestamp'],
            'text': corrected_text
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

def print_low_similarity_mappings(mappings, threshold=0.8):
    """打印相似度低于阈值且字符差值不为0的映射"""
    print("\n相似度低于阈值且存在字符差异的映射:")
    found = False
    
    for mapping in mappings:
        if mapping['similarity'] < threshold and mapping['char_diff'] != 0:
            found = True
            print(f"\n字幕行号: {mapping['subtitle_number']}")
            print(f"字幕: {mapping['subtitle_text']}")
            print(f"原文短句: {mapping['original_segment']}")
            print(f"字符差值: {mapping['char_diff']}")
            print(f"相似度: {mapping['similarity']:.2f}")
            print(f"原文长句: {mapping['original_sentence']}")
            print(f"前一句: {mapping['prev_sentence']}")
            print(f"后一句: {mapping['next_sentence']}")
            print(f"短句集合: {mapping['sentence_segments']}")
            print(f"前一句+原文短句: {mapping['combined_prev_segment']}")
    
    if not found:
        print("未发现相似度低且有字符差异的映射。")

def find_context_sentences(original_text, segment, original_sentence):
    """找出原文短句在原文长句中的前一句和后一句"""
    # 如果原文长句为空或与短句相同，直接返回null
    if not original_sentence or original_sentence == segment:
        return "null", "null"
    
    # 使用各种符号作为分隔符，包括引号和破折号
    delimiters = '，；：、,.;:！？。!?."\'""''「」『』【】《》〈〉—–-…～'
    
    # 1. 首先确定短句在长句中的位置
    start_pos = original_sentence.find(segment)
    
    # 如果直接查找失败，尝试清理后再查找
    if start_pos == -1:
        clean_segment = clean_text_for_comparison(segment)
        clean_sentence = clean_text_for_comparison(original_sentence)
        
        if clean_segment not in clean_sentence:
            return "null", "null"
        
        # 尝试在原句中找到最佳匹配位置
        best_match_pos = -1
        best_match_score = 0
        
        for i in range(len(original_sentence) - len(segment) + 1):
            substr = original_sentence[i:i+len(segment)]
            clean_substr = clean_text_for_comparison(substr)
            
            # 计算相似度
            similarity = difflib.SequenceMatcher(None, clean_segment, clean_substr).ratio()
            if similarity > best_match_score:
                best_match_score = similarity
                best_match_pos = i
        
        if best_match_score > 0.7:  # 设置一个相似度阈值
            start_pos = best_match_pos
        else:
            return "null", "null"
    
    end_pos = start_pos + len(segment)
    
    # 2. 向前查找最近的分隔符
    prev_delimiter_pos = -1
    for i in range(start_pos - 1, -1, -1):
        if original_sentence[i] in delimiters:
            prev_delimiter_pos = i
            break
    
    # 3. 向后查找最近的分隔符
    next_delimiter_pos = len(original_sentence)
    for i in range(end_pos, len(original_sentence)):
        if original_sentence[i] in delimiters:
            next_delimiter_pos = i
            break
    
    # 4. 提取前一句和后一句
    prev_sentence = "null"
    if prev_delimiter_pos >= 0:
        # 再向前找一个分隔符，确定前一句的开始位置
        prev_start_pos = 0
        for i in range(prev_delimiter_pos - 1, -1, -1):
            if original_sentence[i] in delimiters:
                prev_start_pos = i + 1
                break
        
        prev_text = original_sentence[prev_start_pos:prev_delimiter_pos + 1].strip()
        if prev_text:
            prev_sentence = prev_text
    
    next_sentence = "null"
    if next_delimiter_pos < len(original_sentence):
        next_text = original_sentence[end_pos:next_delimiter_pos + 1].strip()
        if next_text:
            next_sentence = next_text
    
    return prev_sentence, next_sentence

def find_original_text(original_text, clean_text):
    """在原文中找到与清理后文本对应的原始文本"""
    # 清理原文用于比较
    clean_original = clean_text_for_comparison(original_text)
    
    # 在清理后的原文中找到清理后文本的位置
    pos = clean_original.find(clean_text)
    if pos == -1:
        return ""
    
    # 计算原文中的对应位置
    original_pos = 0
    clean_pos = 0
    while clean_pos < pos and original_pos < len(original_text):
        if clean_text_for_comparison(original_text[original_pos]) != "":
            clean_pos += 1
        original_pos += 1
    
    # 从原文中提取对应的文本
    start_pos = original_pos
    clean_pos = 0
    while clean_pos < len(clean_text) and original_pos < len(original_text):
        if clean_text_for_comparison(original_text[original_pos]) != "":
            clean_pos += 1
        original_pos += 1
    
    end_pos = original_pos
    return original_text[start_pos:end_pos].strip()

def print_large_char_diff_mappings(mappings, threshold=1):
    """打印字符差值绝对值大于阈值的映射"""
    print(f"\n字符差值绝对值大于{threshold}的映射:")
    found = False
    
    for mapping in mappings:
        if abs(mapping['char_diff']) > threshold:
            found = True
            print(f"\n字幕行号: {mapping['subtitle_number']}")
            print(f"字幕: {mapping['subtitle_text']}")
            print(f"原文短句: {mapping['original_segment']}")
            print(f"字符差值: {mapping['char_diff']}")
            print(f"相似度: {mapping['similarity']:.2f}")
            print(f"原文长句: {mapping['original_sentence']}")
            print(f"前一句: {mapping['prev_sentence']}")
            print(f"后一句: {mapping['next_sentence']}")
            print(f"前一句+原文短句: {mapping['combined_prev_segment']}")
            print(f"原文短句+后一句: {mapping['combined_next_segment']}")
            
            # 直接使用存储的相似度值
            print(f"前一句+原文短句与字幕的相似度: {mapping['combined_similarity']:.2f}")
            print(f"原文短句+后一句与字幕的相似度: {mapping['combined_next_similarity']:.2f}")
            
            # 显示最终选择的版本
            original_sim = mapping['similarity']
            prev_sim = mapping['combined_similarity']
            next_sim = mapping['combined_next_similarity']
            
            best_sim = max(original_sim, prev_sim, next_sim)
            
            if best_sim == next_sim and next_sim > original_sim + 0.05:
                print("✓ 使用原文短句+后一句进行更正（相似度最高）")
            elif best_sim == prev_sim and prev_sim > original_sim + 0.05:
                print("✓ 使用前一句+原文短句进行更正（相似度最高）")
            else:
                print("✓ 使用原文短句进行更正")
    
    if not found:
        print("未发现字符差值绝对值大于阈值的映射。")

def generate_sentence_mapping(original_text_path, srt_path, output_path, corrected_srt_path=None):
    """生成字幕文件语句和原文语句的映射文件，并可选择同时更正字幕"""
    # 读取原始文本
    with open(original_text_path, 'r', encoding='utf-8') as f:
        original_text = f.read().strip()
    
    # 解析SRT文件
    subtitles = parse_srt(srt_path)
    
    # 先分割原文为长句
    # 使用常见的中文和英文句子结束符号，包括引号和破折号
    sentence_delimiters = '[。！？!?"\'""''」』】》〉]'
    original_sentences = re.split(f'({sentence_delimiters})', original_text)
    
    # 重新组合句子和标点
    processed_sentences = []
    i = 0
    while i < len(original_sentences):
        if i + 1 < len(original_sentences) and re.match(sentence_delimiters, original_sentences[i+1]):
            processed_sentences.append((original_sentences[i] + original_sentences[i+1]).strip())
            i += 2
        else:
            if original_sentences[i].strip():  # 只添加非空句子
                processed_sentences.append(original_sentences[i].strip())
            i += 1
    
    # 分割原文为短句
    # 使用更多的分隔符号，包括逗号、分号、顿号、引号和破折号等
    segment_delimiters = '[。，；：！？、,.;:!?"\'""''「」『』【】《》〈〉—–-…～]'
    original_segments = re.split(f'({segment_delimiters})', original_text)
    
    # 重新组合句子和标点
    processed_segments = []
    i = 0
    while i < len(original_segments):
        if i + 1 < len(original_segments) and re.match(segment_delimiters, original_segments[i+1]):
            processed_segments.append((original_segments[i] + original_segments[i+1]).strip())
            i += 2
        else:
            if original_segments[i].strip():  # 只添加非空句子
                processed_segments.append(original_segments[i].strip())
            i += 1
    
    # 过滤太短的片段
    processed_segments = [seg.strip() for seg in processed_segments if len(clean_text_for_comparison(seg)) > 2]
    
    print(f"原文长句数: {len(processed_sentences)}")
    print(f"原文短句数: {len(processed_segments)}")
    
    # 建立短句到长句的映射
    segment_to_sentence = {}
    for segment in processed_segments:
        best_match = None
        best_score = -1
        
        clean_segment = clean_text_for_comparison(segment)
        for sentence in processed_sentences:
            clean_sentence = clean_text_for_comparison(sentence)
            # 如果短句是长句的一部分
            if clean_segment in clean_sentence:
                # 计算短句在长句中的覆盖率
                coverage = len(clean_segment) / len(clean_sentence)
                # 优先选择覆盖率高的长句
                score = len(clean_segment) * (1 + coverage)
                if score > best_score:
                    best_score = score
                    best_match = sentence
        
        if best_match:
            segment_to_sentence[segment] = best_match
    
    # 对每个字幕条目进行处理
    sentence_mappings = []
    # 用于存储字幕更正的映射
    subtitle_corrections = {}
    
    for subtitle in subtitles:
        subtitle_text = subtitle['text'].strip()
        subtitle_number = subtitle['number']  # 获取字幕行号
        if not subtitle_text:  # 跳过空字幕
            continue
            
        # 清理字幕文本用于比较
        clean_subtitle = clean_text_for_comparison(subtitle_text)
        
        # 尝试找到精确匹配的原文短句
        best_match_segment = None
        best_score = -1
        
        # 1. 首先尝试寻找精确匹配的原文短句
        for original_segment in processed_segments:
            clean_original = clean_text_for_comparison(original_segment)
            if not clean_original:  # 跳过空句子
                continue
            
            # 计算相似度 - 使用SequenceMatcher而不是最长公共子串
            similarity = difflib.SequenceMatcher(None, clean_subtitle, clean_original).ratio()
            
            # 计算长度比例
            len_ratio = len(clean_original) / len(clean_subtitle) if len(clean_subtitle) > 0 else 0
            
            # 计算共同字符数
            common_chars = sum(1 for c in clean_subtitle if c in clean_original)
            char_ratio = common_chars / len(clean_subtitle) if len(clean_subtitle) > 0 else 0
            
            # 综合评分：考虑相似度、长度比例和共同字符
            score = (similarity * 0.4 + char_ratio * 0.4 + (1 - abs(1 - len_ratio)) * 0.2) * len(clean_subtitle)
            
            if score > best_score:
                best_score = score
                best_match_segment = original_segment
        
        # 2. 如果没有找到足够好的匹配，尝试部分匹配
        if not best_match_segment or best_score < len(clean_subtitle) * 0.3:  # 如果最佳分数太低
            for original_segment in processed_segments:
                clean_original = clean_text_for_comparison(original_segment)
                if not clean_original:  # 跳过空句子
                    continue
                
                # 计算每个字符的最佳匹配位置
                char_matches = []
                for char in clean_subtitle:
                    best_char_pos = -1
                    best_char_score = 0
                    for i, orig_char in enumerate(clean_original):
                        if char == orig_char:
                            # 考虑位置的相对性
                            pos_score = 1 - abs(i/len(clean_original) - len(char_matches)/len(clean_subtitle))
                            if pos_score > best_char_score:
                                best_char_score = pos_score
                                best_char_pos = i
                    if best_char_pos >= 0:
                        char_matches.append(best_char_pos)
                
                # 计算匹配字符的连续性和覆盖率
                char_coverage = len(char_matches) / len(clean_subtitle)
                if len(char_matches) > 1:
                    continuity = sum(1 for i in range(len(char_matches)-1) 
                                   if char_matches[i+1] - char_matches[i] == 1) / (len(char_matches)-1)
                else:
                    continuity = 0
                
                score = (char_coverage * 0.7 + continuity * 0.3) * len(clean_subtitle)
                
                if score > best_score:
                    best_score = score
                    best_match_segment = original_segment
        
        # 3. 如果仍未找到匹配，尝试组合相邻短句
        if best_match_segment:
            combined_segment, similarity = try_combine_segments(processed_segments, clean_subtitle, best_match_segment)
            if combined_segment:  # 只要有返回结果就使用，因为try_combine_segments已经保证了只在相似度提高时才返回组合结果
                best_match_segment = combined_segment
                best_score = similarity * len(clean_subtitle)  # 更新最佳分数
        
        # 4. 如果到这里还是没有找到匹配，选择最接近的一个
        if not best_match_segment:
            # 使用最基本的字符匹配
            best_match_segment = min(processed_segments, 
                                   key=lambda x: abs(len(clean_text_for_comparison(x)) - len(clean_subtitle)) 
                                   if len(clean_text_for_comparison(x)) > 0 else float('inf'))
            best_score = 0.1  # 给一个很低的分数
        
        # 如果找到了匹配的原文短句
        if best_match_segment:
            # 找到对应的原文长句
            original_sentence = segment_to_sentence.get(best_match_segment)
            if not original_sentence:
                # 如果找不到对应的长句，可能是组合后的短句，需要重新查找
                for sentence in processed_sentences:
                    if clean_text_for_comparison(best_match_segment) in clean_text_for_comparison(sentence):
                        original_sentence = sentence
                        break
            
            if original_sentence:
                # 找到上下文句子
                prev_sentence, next_sentence = find_context_sentences(original_text, best_match_segment, original_sentence)
                
                # 计算字符差异和相似度
                clean_best_match = clean_text_for_comparison(best_match_segment)
                char_diff = len(clean_subtitle) - len(clean_best_match)
                similarity = difflib.SequenceMatcher(None, clean_subtitle, clean_best_match).ratio()
                
                # 获取短句集合
                sentence_segments = []
                current_segment = ""
                for i, char in enumerate(original_sentence):
                    current_segment += char
                    if i + 1 < len(original_sentence) and original_sentence[i+1] in '。，；：！？、,.;:!?':
                        current_segment += original_sentence[i+1]
                        sentence_segments.append(current_segment.strip())
                        current_segment = ""
                if current_segment:
                    sentence_segments.append(current_segment.strip())
                
                # 构建映射信息
                mapping_info = {
                    'subtitle_number': subtitle_number,
                    'subtitle_text': subtitle_text,
                    'original_segment': best_match_segment,
                    'char_diff': char_diff,
                    'similarity': similarity,
                    'original_sentence': original_sentence,
                    'prev_sentence': prev_sentence,
                    'next_sentence': next_sentence,
                    'sentence_segments': '|'.join(sentence_segments),
                    'combined_prev_segment': prev_sentence + best_match_segment if prev_sentence != "null" else best_match_segment
                }
                
                # 计算组合文本的相似度
                combined_text = mapping_info['combined_prev_segment']
                if combined_text != "null" and subtitle_text:
                    clean_combined = clean_text_for_comparison(combined_text)
                    clean_subtitle = clean_text_for_comparison(subtitle_text)
                    combined_similarity = difflib.SequenceMatcher(None, clean_combined, clean_subtitle).ratio()
                    mapping_info['combined_similarity'] = combined_similarity
                else:
                    mapping_info['combined_similarity'] = 0.0
                
                # 计算原文短句+后一句的相似度
                combined_next_text = best_match_segment + next_sentence if next_sentence != "null" else best_match_segment
                mapping_info['combined_next_segment'] = combined_next_text
                if combined_next_text != "null" and subtitle_text:
                    clean_combined_next = clean_text_for_comparison(combined_next_text)
                    clean_subtitle = clean_text_for_comparison(subtitle_text)
                    combined_next_similarity = difflib.SequenceMatcher(None, clean_combined_next, clean_subtitle).ratio()
                    mapping_info['combined_next_similarity'] = combined_next_similarity
                else:
                    mapping_info['combined_next_similarity'] = 0.0
                
                sentence_mappings.append(mapping_info)
                
                # 如果需要更正字幕，存储映射关系
                if corrected_srt_path:
                    # 选择相似度最高的版本
                    original_sim = mapping_info['similarity']
                    prev_sim = mapping_info['combined_similarity']
                    next_sim = mapping_info['combined_next_similarity']
                    
                    best_sim = max(original_sim, prev_sim, next_sim)
                    
                    if best_sim == next_sim and next_sim > original_sim + 0.05:
                        subtitle_corrections[subtitle_number] = mapping_info['combined_next_segment']
                    elif best_sim == prev_sim and prev_sim > original_sim + 0.05:
                        subtitle_corrections[subtitle_number] = mapping_info['combined_prev_segment']
                    else:
                        subtitle_corrections[subtitle_number] = best_match_segment
        
        else:
            # 如果没有找到匹配，记录空映射
            mapping_info = {
                'subtitle_number': subtitle_number,
                'subtitle_text': subtitle_text,
                'original_segment': "未找到匹配",
                'char_diff': 0,
                'similarity': 0,
                'original_sentence': "未找到匹配",
                'prev_sentence': "null",
                'next_sentence': "null",
                'sentence_segments': "",
                'combined_prev_segment': ""
            }
            sentence_mappings.append(mapping_info)
    
    # 写入映射文件
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入表头
        f.write("字幕行号\t字幕\t原文短句\t字符差值\t相似度\t原文长句\t前一句\t后一句\t短句集合\t前一句+原文短句\n")
        # 写入映射数据
        for mapping in sentence_mappings:
            f.write(f"{mapping['subtitle_number']}\t{mapping['subtitle_text']}\t{mapping['original_segment']}\t"
                   f"{mapping['char_diff']}\t{mapping['similarity']:.2f}\t{mapping['original_sentence']}\t"
                   f"{mapping['prev_sentence']}\t{mapping['next_sentence']}\t{mapping['sentence_segments']}\t"
                   f"{mapping['combined_prev_segment']}\n")
    
    print(f"映射文件已生成：{output_path}")
    
    # 生成最终修正映射文件
    corrected_mapping_path = os.path.join(os.path.dirname(output_path), 
                                        os.path.splitext(os.path.basename(output_path))[0] + "_final.txt")
    
    with open(corrected_mapping_path, 'w', encoding='utf-8') as f:
        # 写入表头
        f.write("字幕行号\t字幕\t修正文本\t使用类型\t原相似度\t修正后相似度\n")
        # 写入映射数据
        for mapping in sentence_mappings:
            subtitle_number = mapping['subtitle_number']
            subtitle_text = mapping['subtitle_text']
            original_similarity = mapping['similarity']
            prev_similarity = mapping.get('combined_similarity', 0.0)
            next_similarity = mapping.get('combined_next_similarity', 0.0)
            
            # 确定使用的文本和类型
            best_sim = max(original_similarity, prev_similarity, next_similarity)
            
            if best_sim == next_similarity and next_similarity > original_similarity + 0.05:
                corrected_text = mapping['combined_next_segment']
                use_type = "原文短句+后一句"
                final_similarity = next_similarity
            elif best_sim == prev_similarity and prev_similarity > original_similarity + 0.05:
                corrected_text = mapping['combined_prev_segment']
                use_type = "前一句+原文短句"
                final_similarity = prev_similarity
            else:
                corrected_text = mapping['original_segment']
                use_type = "原文短句"
                final_similarity = original_similarity
            
            f.write(f"{subtitle_number}\t{subtitle_text}\t{corrected_text}\t{use_type}\t"
                   f"{original_similarity:.2f}\t{final_similarity:.2f}\n")
    
    print(f"最终修正映射文件已生成：{corrected_mapping_path}")
    
    # 分析字符差值较大的映射
    print("\n分析字符差值较大的映射...")
    print_large_char_diff_mappings(sentence_mappings)
    
    # 如果需要生成更正后的字幕文件
    if corrected_srt_path and subtitle_corrections:
        corrected_subtitles = []
        for subtitle in subtitles:
            corrected_text = subtitle_corrections.get(subtitle['number'], subtitle['text'])
            corrected_subtitles.append({
                'number': subtitle['number'],
                'timestamp': subtitle['timestamp'],
                'text': corrected_text
            })
        
        # 写入更正后的字幕文件
        with open(corrected_srt_path, 'w', encoding='utf-8') as f:
            for subtitle in corrected_subtitles:
                f.write(f"{subtitle['number']}\n")
                f.write(f"{subtitle['timestamp']}\n")
                f.write(f"{subtitle['text']}\n\n")
        
        print(f"更正后的字幕文件已生成：{corrected_srt_path}")
    
    return sentence_mappings

def try_combine_segments(segments, clean_subtitle, current_match):
    """尝试将相邻的短句组合，看是否能提高匹配度"""
    if not current_match:
        return None, 0

    current_index = segments.index(current_match)
    best_combined = None
    best_similarity = difflib.SequenceMatcher(None, clean_text_for_comparison(current_match), clean_subtitle).ratio()
    
    # 向前组合
    if current_index > 0:
        prev_segment = segments[current_index - 1]
        # 尝试多种组合方式
        combinations = [
            prev_segment + current_match,  # 直接拼接
            prev_segment + "，" + current_match,  # 用逗号连接
            prev_segment.rstrip('，。、') + current_match  # 去掉前句的标点后拼接
        ]
        
        for combined in combinations:
            similarity = difflib.SequenceMatcher(None, clean_text_for_comparison(combined), clean_subtitle).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_combined = combined

    # 向后组合
    if current_index < len(segments) - 1:
        next_segment = segments[current_index + 1]
        # 尝试多种组合方式
        combinations = [
            current_match + next_segment,  # 直接拼接
            current_match + "，" + next_segment,  # 用逗号连接
            current_match.rstrip('，。、') + next_segment  # 去掉当前句的标点后拼接
        ]
        
        for combined in combinations:
            similarity = difflib.SequenceMatcher(None, clean_text_for_comparison(combined), clean_subtitle).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_combined = combined

    # 尝试三句组合（前句+当前句+后句）
    if current_index > 0 and current_index < len(segments) - 1:
        prev_segment = segments[current_index - 1]
        next_segment = segments[current_index + 1]
        # 尝试多种三句组合方式
        combinations = [
            prev_segment + current_match + next_segment,  # 直接拼接
            prev_segment + "，" + current_match + "，" + next_segment,  # 用逗号连接
            prev_segment.rstrip('，。、') + current_match.rstrip('，。、') + next_segment  # 去掉标点后拼接
        ]
        
        for combined in combinations:
            similarity = difflib.SequenceMatcher(None, clean_text_for_comparison(combined), clean_subtitle).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_combined = combined

    # 如果找到更好的组合就返回
    if best_combined:
        return best_combined, best_similarity

    return None, best_similarity

def longest_common_substring(str1, str2):
    """计算两个字符串的最长公共子串长度"""
    m, n = len(str1), len(str2)
    # 创建DP表
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # 记录最长子串的长度
    max_length = 0
    
    # 填充DP表
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
                max_length = max(max_length, dp[i][j])
    
    return max_length

def extract_best_matching_subsegment(segment, subtitle_text):
    """从原文短句中提取与字幕最匹配的部分"""
    # 清理文本用于比较
    clean_segment = clean_text_for_comparison(segment)
    clean_subtitle = clean_text_for_comparison(subtitle_text)
    
    # 如果字幕文本是原文短句的一部分，直接返回字幕文本对应的原文部分
    if clean_subtitle in clean_segment:
        # 找到字幕在原文中的位置
        start_pos = clean_segment.find(clean_subtitle)
        end_pos = start_pos + len(clean_subtitle)
        
        # 提取原文中对应的部分，保留标点符号
        segment_chars = list(segment)
        clean_chars = []
        original_to_clean_map = {}
        
        # 建立原文字符到清理后字符的映射
        clean_index = 0
        for i, char in enumerate(segment):
            if char.isalnum() or '\u4e00' <= char <= '\u9fff':  # 字母、数字或中文字符
                clean_chars.append(char)
                original_to_clean_map[clean_index] = i
                clean_index += 1
        
        # 根据清理后的索引找到原文中的对应位置
        if start_pos in original_to_clean_map and end_pos - 1 in original_to_clean_map:
            orig_start = original_to_clean_map[start_pos]
            orig_end = original_to_clean_map[end_pos - 1] + 1
            
            # 扩展边界，包含相邻的标点符号
            while orig_start > 0 and not (segment_chars[orig_start-1].isalnum() or '\u4e00' <= segment_chars[orig_start-1] <= '\u9fff'):
                orig_start -= 1
            
            while orig_end < len(segment_chars) and not (segment_chars[orig_end].isalnum() or '\u4e00' <= segment_chars[orig_end] <= '\u9fff'):
                orig_end += 1
            
            return segment[orig_start:orig_end]
    
    # 如果无法精确定位，返回原始短句
    return segment

def longest_common_subsequence(str1, str2):
    """计算两个字符串的最长公共子序列长度，用于句子相似度计算"""
    m, n = len(str1), len(str2)
    # 创建DP表
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # 填充DP表
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

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

def correct_srt_from_mapping(srt_path, mapping_path, output_path):
    """根据字幕和原文短句的映射生成更正后的字幕"""
    print(f"使用映射文件 {mapping_path} 更正字幕 {srt_path}...")
    
    # 解析SRT文件
    subtitles = parse_srt(srt_path)
    
    # 加载映射文件
    mappings = {}
    with open(mapping_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:  # 确保至少有字幕文本和原文短句
                subtitle_text = parts[0]
                original_segment = parts[1]
                # 将字幕文本映射到原文短句
                mappings[subtitle_text] = original_segment
    
    print(f"加载了 {len(mappings)} 条映射记录")
    
    # 更正字幕
    corrected_count = 0
    corrected_subtitles = []
    
    for subtitle in subtitles:
        subtitle_text = subtitle['text'].strip()
        if subtitle_text in mappings:
            # 使用映射中的原文短句替换字幕文本
            corrected_text = mappings[subtitle_text].strip()  # 确保没有前后空格
            if corrected_text != subtitle_text:
                corrected_count += 1
            
            corrected_subtitles.append({
                'number': subtitle['number'],
                'timestamp': subtitle['timestamp'],
                'text': corrected_text
            })
        else:
            # 如果没有找到映射，保留原始字幕
            corrected_subtitles.append(subtitle)
    
    # 写入更正后的SRT文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for subtitle in corrected_subtitles:
            # 确保每个字段都没有多余的空格
            f.write(f"{subtitle['number']}\n")
            f.write(f"{subtitle['timestamp']}\n")
            f.write(f"{subtitle['text'].strip()}\n\n")  # 确保文本没有前后空格
    
    print(f"\n更正完成！")
    print(f"输出文件：{output_path}")
    print(f"总字幕条数：{len(corrected_subtitles)}")
    print(f"更正条数：{corrected_count}")
    print(f"更正率：{corrected_count/len(corrected_subtitles)*100:.1f}%")
    
    return corrected_subtitles

def main():
    parser = argparse.ArgumentParser(description='字幕纠错工具 - 基于字符映射和句子映射的纠错算法')
    parser.add_argument('srt_file', help='需要纠正的SRT字幕文件路径')
    parser.add_argument('original_text', help='原始文本文件路径', nargs='?')
    parser.add_argument('-o', '--output', help='输出的纠正后SRT文件路径（默认在原SRT文件目录生成）')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细对比信息')
    parser.add_argument('--show-all', action='store_true', help='显示所有字幕对比（默认只显示前10条）')
    parser.add_argument('--char-mapping', help='指定字符级别的映射文件路径')
    parser.add_argument('--sentence-mapping', help='指定句子级别的映射文件路径')
    parser.add_argument('--generate-only', action='store_true', help='仅生成映射文件，不进行字幕更正')
    
    args = parser.parse_args()
    
    # 设置输出文件路径
    if args.output:
        output_file = args.output
    else:
        srt_dir = os.path.dirname(args.srt_file)
        srt_name = os.path.splitext(os.path.basename(args.srt_file))[0]
        output_file = os.path.join(srt_dir, f"{srt_name}_corrected.srt")
    
    # 检查SRT文件是否存在
    if not os.path.exists(args.srt_file):
        print(f"错误：SRT字幕文件不存在：{args.srt_file}")
        sys.exit(1)
    
    # 如果指定了映射文件，则使用映射文件进行更正
    if args.char_mapping or args.sentence_mapping:
        corrected_subtitles = None
        
        # 如果指定了字符映射文件，先应用字符映射
        if args.char_mapping:
            if not os.path.exists(args.char_mapping):
                print(f"错误：字符映射文件不存在：{args.char_mapping}")
                sys.exit(1)
            
            print(f"使用字符映射文件进行更正：{args.char_mapping}")
            # 加载字符映射
            mapping_dict = load_character_mapping(args.char_mapping)
            
            # 解析SRT文件
            subtitles = parse_srt(args.srt_file)
            
            # 应用字符映射进行更正
            corrected_subtitles = []
            corrected_count = 0
            
            for subtitle in subtitles:
                corrected_text = apply_character_mapping(subtitle['text'], mapping_dict).strip()  # 确保没有前后空格
                if corrected_text != subtitle['text']:
                    corrected_count += 1
                
                corrected_subtitles.append({
                    'number': subtitle['number'],
                    'timestamp': subtitle['timestamp'],
                    'text': corrected_text
                })
            
            print(f"字符映射更正完成，更正了 {corrected_count} 条字幕")
            
            # 如果只有字符映射，直接写入输出文件
            if not args.sentence_mapping:
                # 写入更正后的SRT文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    for subtitle in corrected_subtitles:
                        # 确保每个字段都没有多余的空格
                        f.write(f"{subtitle['number']}\n")
                        f.write(f"{subtitle['timestamp']}\n")
                        f.write(f"{subtitle['text'].strip()}\n\n")  # 确保文本没有前后空格
                
                print(f"输出文件：{output_file}")
        
        # 如果指定了句子映射文件，应用句子映射
        if args.sentence_mapping:
            if not os.path.exists(args.sentence_mapping):
                print(f"错误：句子映射文件不存在：{args.sentence_mapping}")
                sys.exit(1)
            
            print(f"使用句子映射文件进行更正：{args.sentence_mapping}")
            
            # 如果之前已经应用了字符映射，创建临时SRT文件
            temp_srt_file = args.srt_file
            if corrected_subtitles:
                temp_srt_file = os.path.join(os.path.dirname(args.srt_file), f"temp_{os.path.basename(args.srt_file)}")
                with open(temp_srt_file, 'w', encoding='utf-8') as f:
                    for subtitle in corrected_subtitles:
                        # 确保每个字段都没有多余的空格
                        f.write(f"{subtitle['number']}\n")
                        f.write(f"{subtitle['timestamp']}\n")
                        f.write(f"{subtitle['text'].strip()}\n\n")  # 确保文本没有前后空格
            
            # 使用句子映射文件更正字幕
            corrected_subtitles = correct_srt_from_mapping(temp_srt_file, args.sentence_mapping, output_file)
            
            # 如果创建了临时文件，删除它
            if temp_srt_file != args.srt_file and os.path.exists(temp_srt_file):
                os.remove(temp_srt_file)
        
        # 显示对比信息
        if args.verbose:
            print("\n=== 更正对比 ===")
            # 解析原始字幕以便比较
            original_subtitles = parse_srt(args.srt_file)
            show_count = len(corrected_subtitles) if args.show_all else 10
            
            for i, subtitle in enumerate(corrected_subtitles[:show_count]):
                if i < len(original_subtitles) and subtitle['text'] != original_subtitles[i]['text']:
                    print(f"\n第{i+1}条 [{subtitle['timestamp']}] - 已更正:")
                    print(f"  原始：{original_subtitles[i]['text']}")
                    print(f"  更正：{subtitle['text']}")
                else:
                    print(f"\n第{i+1}条 [{subtitle['timestamp']}] - 无需更正:")
                    print(f"  文本：{subtitle['text']}")
            
            if not args.show_all and len(corrected_subtitles) > 10:
                print(f"\n... 还有 {len(corrected_subtitles) - 10} 条字幕，使用 --show-all 查看全部")
        
        return
    
    # 如果没有指定映射文件，但提供了原始文本，则生成映射并更正
    if args.original_text:
        if not os.path.exists(args.original_text):
            print(f"错误：原始文本文件不存在：{args.original_text}")
            sys.exit(1)
        
        # 设置映射文件路径
        srt_dir = os.path.dirname(args.srt_file)
        srt_name = os.path.splitext(os.path.basename(args.srt_file))[0]
        char_mapping_file = os.path.join(srt_dir, f"{srt_name}_char_mapping.txt")
        sentence_mapping_file = os.path.join(srt_dir, f"{srt_name}_sentence_mapping.txt")
        
        print("开始生成映射文件...")
        print(f"原始文本：{args.original_text}")
        print(f"SRT文件：{args.srt_file}")
        
        # 生成字符映射
        print("\n生成字符级别映射...")
        generate_character_mapping(args.original_text, args.srt_file, char_mapping_file)
        
        # 生成句子映射
        print("\n生成句子级别映射...")
        
        # 如果只需要生成映射文件，不进行字幕更正
        if args.generate_only:
            generate_sentence_mapping(args.original_text, args.srt_file, sentence_mapping_file)
            print(f"\n映射文件已生成：")
            print(f"字符映射：{char_mapping_file}")
            print(f"句子映射：{sentence_mapping_file}")
            return
        
        # 否则，生成映射的同时进行字幕更正
        print(f"同时应用映射进行字幕更正，输出到：{output_file}")
        result = generate_sentence_mapping(args.original_text, args.srt_file, sentence_mapping_file, output_file)
        
        if isinstance(result, tuple):
            _, corrected_subtitles = result
        
            # 显示对比信息
            if args.verbose:
                print("\n=== 更正对比 ===")
                # 解析原始字幕以便比较
                original_subtitles = parse_srt(args.srt_file)
                show_count = len(corrected_subtitles) if args.show_all else 10
                
                for i, subtitle in enumerate(corrected_subtitles[:show_count]):
                    if i < len(original_subtitles) and subtitle['text'] != original_subtitles[i]['text']:
                        print(f"\n第{i+1}条 [{subtitle['timestamp']}] - 已更正:")
                        print(f"  原始：{original_subtitles[i]['text']}")
                        print(f"  更正：{subtitle['text']}")
                    else:
                        print(f"\n第{i+1}条 [{subtitle['timestamp']}] - 无需更正:")
                        print(f"  文本：{subtitle['text']}")
                
                if not args.show_all and len(corrected_subtitles) > 10:
                    print(f"\n... 还有 {len(corrected_subtitles) - 10} 条字幕，使用 --show-all 查看全部")
        
        return
    
    # 如果既没有指定映射文件，也没有提供原始文本，则显示错误信息
    print("错误：请指定映射文件(--char-mapping 和/或 --sentence-mapping)或提供原始文本文件")
    sys.exit(1)

if __name__ == "__main__":
    main()