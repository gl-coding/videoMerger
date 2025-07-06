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
    """打印相似度低于阈值的映射"""
    print("\n相似度低于 {:.2f} 的映射:".format(threshold))
    print("-" * 80)
    low_similarity_count = 0
    
    for subtitle_text, original_segment, char_diff, similarity, original_sentence in mappings:
        if similarity < threshold:
            low_similarity_count += 1
            print(f"字幕: {subtitle_text}")
            print(f"原文短句: {original_segment}")
            print(f"字符差值: {char_diff}")
            print(f"相似度: {similarity:.2f}")
            print(f"原文长句: {original_sentence}")
            print("-" * 80)
    
    print(f"总共有 {low_similarity_count} 个相似度低于 {threshold} 的映射")

def generate_sentence_mapping(original_text_path, srt_path, output_path, corrected_srt_path=None):
    """生成字幕文件语句和原文语句的映射文件，并可选择同时更正字幕"""
    # 读取原始文本
    with open(original_text_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    # 解析SRT文件
    subtitles = parse_srt(srt_path)
    
    # 先分割原文为长句
    # 使用常见的中文和英文句子结束符号
    original_sentences = re.split(r'([。！？!?])', original_text)
    # 重新组合句子和标点
    processed_sentences = []
    i = 0
    while i < len(original_sentences):
        if i + 1 < len(original_sentences) and original_sentences[i+1] in '。！？!?':
            processed_sentences.append(original_sentences[i] + original_sentences[i+1])
            i += 2
        else:
            if original_sentences[i].strip():  # 只添加非空句子
                processed_sentences.append(original_sentences[i])
            i += 1
    
    # 分割原文为短句
    # 使用更多的分隔符号，包括逗号、分号等
    original_segments = re.split(r'([。，；：！？,.;:!?])', original_text)
    # 重新组合句子和标点
    processed_segments = []
    i = 0
    while i < len(original_segments):
        if i + 1 < len(original_segments) and original_segments[i+1] in '。，；：！？,.;:!?':
            processed_segments.append(original_segments[i] + original_segments[i+1])
            i += 2
        else:
            if original_segments[i].strip():  # 只添加非空句子
                processed_segments.append(original_segments[i])
            i += 1
    
    # 过滤太短的片段
    processed_segments = [seg for seg in processed_segments if len(clean_text_for_comparison(seg)) > 2]
    
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
            
            # 计算精确匹配度 - 使用最长公共子串而非子序列
            lcs = longest_common_substring(clean_subtitle, clean_original)
            match_ratio = lcs / len(clean_subtitle)
            
            # 如果匹配度高且长度接近，视为精确匹配
            if match_ratio > 0.8 and 0.7 <= len(clean_original) / len(clean_subtitle) <= 1.3:
                score = lcs * 3  # 给精确匹配更高的分数
                if score > best_score:
                    best_score = score
                    best_match_segment = original_segment
        
        # 2. 如果没有找到精确匹配，尝试找到包含字幕内容的最小原文短句
        if not best_match_segment:
            for original_segment in processed_segments:
                clean_original = clean_text_for_comparison(original_segment)
                if not clean_original:  # 跳过空句子
                    continue
                
                # 如果原文短句包含字幕文本
                if clean_subtitle in clean_original:
                    # 计算包含率 - 越接近1越好
                    contain_ratio = len(clean_subtitle) / len(clean_original)
                    score = len(clean_subtitle) * (contain_ratio ** 2)  # 给包含率高的更高分数
                    if score > best_score:
                        best_score = score
                        best_match_segment = original_segment
        
        # 3. 如果仍未找到匹配，使用最长公共子序列
        if not best_match_segment:
            for original_segment in processed_segments:
                clean_original = clean_text_for_comparison(original_segment)
                if not clean_original:  # 跳过空句子
                    continue
                    
                # 计算最长公共子序列长度作为相似度
                score = longest_common_subsequence(clean_subtitle, clean_original)
                if score > best_score:
                    best_score = score
                    best_match_segment = original_segment
        
        # 4. 检查是否需要合并多个短句来匹配字幕
        if best_match_segment:
            clean_segment = clean_text_for_comparison(best_match_segment)
            # 如果最佳匹配只覆盖了字幕的一部分（小于70%）
            if longest_common_subsequence(clean_subtitle, clean_segment) < len(clean_subtitle) * 0.7:
                # 尝试合并相邻短句
                combined_segment = try_combine_segments(processed_segments, clean_subtitle, best_match_segment)
                if combined_segment != best_match_segment:
                    best_match_segment = combined_segment
        
        if best_match_segment:
            # 计算相似度
            clean_subtitle = clean_text_for_comparison(subtitle_text)
            clean_segment = clean_text_for_comparison(best_match_segment)
            
            # 使用最长公共子序列计算相似度
            lcs_score = longest_common_subsequence(clean_subtitle, clean_segment)
            similarity = lcs_score / max(len(clean_subtitle), 1)
            
            # 计算字符数差异
            char_diff = len(clean_segment) - len(clean_subtitle)
            
            # 只有相似度超过阈值才添加映射
            if similarity > 0.3:  # 设置一个相似度阈值
                # 找到对应的长句
                best_match_sentence = segment_to_sentence.get(best_match_segment)
                if not best_match_sentence:  # 如果没有找到对应的长句，使用短句作为长句
                    best_match_sentence = best_match_segment
                
                # 5. 如果匹配的短句明显长于字幕，尝试找到更精确的子句
                if len(clean_segment) > len(clean_subtitle) * 1.5:
                    # 尝试从短句中提取与字幕最匹配的部分
                    extracted_segment = extract_best_matching_subsegment(best_match_segment, subtitle_text)
                    
                    # 只有当提取的部分覆盖了字幕的大部分内容时才使用
                    extracted_clean = clean_text_for_comparison(extracted_segment)
                    if longest_common_subsequence(clean_subtitle, extracted_clean) >= len(clean_subtitle) * 0.7:
                        best_match_segment = extracted_segment
                        # 重新计算相似度
                        clean_segment = clean_text_for_comparison(best_match_segment)
                        lcs_score = longest_common_subsequence(clean_subtitle, clean_segment)
                        similarity = lcs_score / max(len(clean_subtitle), 1)
                        # 重新计算字符数差异
                        char_diff = len(clean_segment) - len(clean_subtitle)
                
                sentence_mappings.append((subtitle_text, best_match_segment, char_diff, similarity, best_match_sentence))
                
                # 保存字幕更正映射
                subtitle_corrections[subtitle_text] = best_match_segment
    
    # 写入映射文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for subtitle_sentence, original_segment, char_diff, similarity, original_sentence in sentence_mappings:
            # 替换制表符和换行符，避免格式混乱
            subtitle_sentence = subtitle_sentence.replace('\t', ' ').replace('\n', ' ')
            original_segment = original_segment.replace('\t', ' ').replace('\n', ' ')
            original_sentence = original_sentence.replace('\t', ' ').replace('\n', ' ')
            
            # 确保原文长句不包含多个句子（通过检查句号、感叹号、问号）
            if '。' in original_sentence or '！' in original_sentence or '？' in original_sentence:
                # 如果包含多个句子结束符，只保留第一个完整句子
                sentence_end = max(
                    original_sentence.find('。') if '。' in original_sentence else -1,
                    original_sentence.find('！') if '！' in original_sentence else -1,
                    original_sentence.find('？') if '？' in original_sentence else -1
                )
                if sentence_end > 0:
                    original_sentence = original_sentence[:sentence_end+1]
            
            f.write(f"{subtitle_sentence}\t{original_segment}\t{char_diff}\t{similarity:.2f}\t{original_sentence}\n")
    
    print(f"句子映射文件已生成：{output_path}")
    print(f"总映射条数：{len(sentence_mappings)}")
    
    # 打印相似度低的映射
    print_low_similarity_mappings(sentence_mappings, 0.8)
    
    # 如果指定了更正字幕的输出路径，则应用映射进行更正
    if corrected_srt_path:
        print(f"\n开始应用映射更正字幕...")
        corrected_count = 0
        corrected_subtitles = []
        
        for subtitle in subtitles:
            subtitle_text = subtitle['text'].strip()
            if subtitle_text in subtitle_corrections:
                # 使用映射中的原文短句替换字幕文本
                corrected_text = subtitle_corrections[subtitle_text].strip()  # 确保没有前后空格
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
        with open(corrected_srt_path, 'w', encoding='utf-8') as f:
            for subtitle in corrected_subtitles:
                # 确保每个字段都没有多余的空格
                f.write(f"{subtitle['number']}\n")
                f.write(f"{subtitle['timestamp']}\n")
                f.write(f"{subtitle['text'].strip()}\n\n")  # 确保文本没有前后空格
        
        print(f"字幕更正完成！")
        print(f"输出文件：{corrected_srt_path}")
        print(f"总字幕条数：{len(corrected_subtitles)}")
        print(f"更正条数：{corrected_count}")
        print(f"更正率：{corrected_count/len(corrected_subtitles)*100:.1f}%")
        
        return sentence_mappings, corrected_subtitles
    
    return sentence_mappings

def try_combine_segments(processed_segments, clean_subtitle, best_match_segment):
    """尝试合并相邻短句以更好地匹配字幕内容"""
    if best_match_segment not in processed_segments:
        return best_match_segment
    
    segment_index = processed_segments.index(best_match_segment)
    combined_segment = best_match_segment
    best_score = longest_common_subsequence(clean_subtitle, clean_text_for_comparison(combined_segment))
    
    # 尝试向后合并最多3个短句
    for i in range(1, 4):
        if segment_index + i < len(processed_segments):
            next_segment = processed_segments[segment_index + i]
            new_combined = combined_segment + next_segment
            new_score = longest_common_subsequence(clean_subtitle, clean_text_for_comparison(new_combined))
            
            # 如果合并后的匹配度显著提高，则采用合并结果
            if new_score > best_score * 1.2:  # 要求至少提高20%
                combined_segment = new_combined
                best_score = new_score
    
    return combined_segment

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