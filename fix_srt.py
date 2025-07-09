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

def preprocess_text(text):
    """预处理文本，标准化但保留句子结构"""
    replacements = {
        '三千': '3000', '两千五': '2500', '一千': '1000',
        '二千': '2000', '四千': '4000', '五千': '5000',
    }
    for cn_num, ar_num in replacements.items():
        text = text.replace(cn_num, ar_num)
    return text

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

def generate_character_mapping(original_text_path, srt_path, mapping_output_path):
    """生成字符级别的一对一映射文件"""
    with open(original_text_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    subtitles = parse_srt(srt_path)
    original_clean = clean_text_for_comparison(preprocess_text(original_text))
    
    all_subtitle_text = "".join(subtitle['text'] for subtitle in subtitles)
    subtitle_clean = clean_text_for_comparison(preprocess_text(all_subtitle_text))
    
    print(f"原始文本长度：{len(original_clean)} 字符")
    print(f"字幕文本长度：{len(subtitle_clean)} 字符")
    
    mappings = []
    
    if len(original_clean) == len(subtitle_clean):
        direct_matches = sum(1 for i in range(len(original_clean)) if original_clean[i] == subtitle_clean[i])
        match_rate = direct_matches / len(original_clean)
        print(f"直接映射匹配率: {match_rate:.1%}")
        
        if match_rate >= 0.7:
            mappings = [f"{subtitle_clean[i]}\t{original_clean[i]}" for i in range(len(original_clean))]
        else:
            mappings = create_sliding_window_mapping(original_clean, subtitle_clean)
    else:
        mappings = create_sliding_window_mapping(original_clean, subtitle_clean)
    
    with open(mapping_output_path, 'w', encoding='utf-8') as f:
        for mapping in mappings:
            f.write(mapping + '\n')
    
    print(f"字符映射文件已生成：{mapping_output_path}")
    return mappings

def create_sliding_window_mapping(original_clean, subtitle_clean):
    """使用滑动窗口创建字符映射"""
    mappings = []
    window_sizes = [50, 100, 200]
    best_alignment = 0
    best_score = 0
    
    for window_size in window_sizes:
        window_size = min(window_size, len(subtitle_clean), len(original_clean))
        if window_size < 10:
            continue
        
        best_pos = 0
        best_window_score = 0
        
        max_search = len(original_clean) - window_size + 1
        for start_pos in range(min(max_search, 100)):
            score = sum(1 for i in range(window_size) 
                       if i < len(subtitle_clean) and start_pos + i < len(original_clean) 
                       and original_clean[start_pos + i] == subtitle_clean[i])
            
            if score > best_window_score:
                best_window_score = score
                best_pos = start_pos
        
        window_match_rate = best_window_score / window_size
        if window_match_rate > best_score:
            best_score = window_match_rate
            best_alignment = best_pos
    
    # 创建映射
    i = j = 0
    while i < len(original_clean):
        if j >= len(subtitle_clean):
            mappings.append(f"{original_clean[i]}\t{original_clean[i]}")
            i += 1
            continue
        
        # 前向匹配检查
        forward_match = sum(1 for k in range(3) 
                          if (i + k < len(original_clean) and 
                              j + k < len(subtitle_clean) and 
                              original_clean[i + k] == subtitle_clean[j + k]))
        
        if forward_match >= 2:
            mappings.append(f"{subtitle_clean[j]}\t{original_clean[i]}")
            i += 1
            j += 1
        else:
            mappings.append(f"{original_clean[i]}\t{original_clean[i]}")
            i += 1
    
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
                    mapping_dict[parts[0]] = parts[1]
    return mapping_dict

def apply_character_mapping(text, mapping_dict):
    """根据字符映射纠正文本"""
    return ''.join(mapping_dict.get(char, char) for char in text)

def find_context_sentences(original_text, segment, original_sentence):
    """找出原文短句在原文长句中的前一句和后一句"""
    if not original_sentence or original_sentence == segment:
        return "null", "null"
    
    delimiters = '，；：、,.;:！？。!?."\'""''「」『』【】《》〈〉—–-…～'
    
    start_pos = original_sentence.find(segment)
    if start_pos == -1:
        return "null", "null"
    
    end_pos = start_pos + len(segment)
    
    # 向前查找分隔符
    prev_delimiter_pos = -1
    for i in range(start_pos - 1, -1, -1):
        if original_sentence[i] in delimiters:
            prev_delimiter_pos = i
            break
    
    # 向后查找分隔符
    next_delimiter_pos = len(original_sentence)
    for i in range(end_pos, len(original_sentence)):
        if original_sentence[i] in delimiters:
            next_delimiter_pos = i
            break
    
    # 提取前一句和后一句
    prev_sentence = "null"
    if prev_delimiter_pos >= 0:
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

def find_best_multi_segment_combination(processed_segments, best_match_segment, subtitle_text, max_segments=3):
    """查找最佳的多短句组合，支持向前向后扩展多个短句"""
    if not best_match_segment or best_match_segment not in processed_segments:
        return best_match_segment, 0.0
    
    current_index = processed_segments.index(best_match_segment)
    clean_subtitle = clean_text_for_comparison(subtitle_text)
    
    # 计算原始短句的相似度作为基准
    clean_original = clean_text_for_comparison(best_match_segment)
    original_similarity = difflib.SequenceMatcher(None, clean_subtitle, clean_original).ratio()
    
    best_combination = best_match_segment
    best_similarity = original_similarity
    
    # 尝试不同的组合策略
    combinations_to_try = []
    
    # 1. 向前扩展（1-3个短句）
    for i in range(1, min(max_segments + 1, current_index + 1)):
        start_idx = current_index - i
        combined_segments = processed_segments[start_idx:current_index + 1]
        combined_text = ''.join(combined_segments)
        combinations_to_try.append(combined_text)
    
    # 2. 向后扩展（1-3个短句）
    for i in range(1, min(max_segments + 1, len(processed_segments) - current_index)):
        end_idx = current_index + i + 1
        combined_segments = processed_segments[current_index:end_idx]
        combined_text = ''.join(combined_segments)
        combinations_to_try.append(combined_text)
    
    # 3. 向前向后同时扩展
    for front in range(1, min(max_segments, current_index + 1)):
        for back in range(1, min(max_segments, len(processed_segments) - current_index)):
            if front + back <= max_segments:
                start_idx = current_index - front
                end_idx = current_index + back + 1
                combined_segments = processed_segments[start_idx:end_idx]
                combined_text = ''.join(combined_segments)
                combinations_to_try.append(combined_text)
    
    # 4. 特殊处理：寻找包含关键词的组合
    for i in range(max(0, current_index - max_segments), min(len(processed_segments), current_index + max_segments + 1)):
        for j in range(i + 1, min(len(processed_segments) + 1, i + max_segments + 1)):
            if i <= current_index < j:  # 确保包含原始匹配段
                combined_segments = processed_segments[i:j]
                combined_text = ''.join(combined_segments)
                combinations_to_try.append(combined_text)
    
    # 评估所有组合
    for combined_text in set(combinations_to_try):  # 去重
        if combined_text == best_match_segment:
            continue
        
        clean_combined = clean_text_for_comparison(combined_text)
        similarity = difflib.SequenceMatcher(None, clean_subtitle, clean_combined).ratio()
        
        # 如果相似度提高，就使用这个组合
        if similarity > best_similarity:
            best_similarity = similarity
            best_combination = combined_text
    
    return best_combination, best_similarity

def generate_sentence_mapping(original_text_path, srt_path, output_path, corrected_srt_path=None):
    """生成字幕文件语句和原文语句的映射文件，并可选择同时更正字幕"""
    with open(original_text_path, 'r', encoding='utf-8') as f:
        original_text = f.read().strip()
    
    subtitles = parse_srt(srt_path)
    
    # 分割原文为长句和短句
    sentence_delimiters = '[。！？!?]'  # 只使用句子终结符
    segment_delimiters = '[。，；：！？、,.;:!?"\'""''「」『』【】《》〈〉—–-…～]'
    
    original_sentences = re.split(f'({sentence_delimiters})', original_text)
    processed_sentences = []
    i = 0
    while i < len(original_sentences):
        if i + 1 < len(original_sentences) and re.match(sentence_delimiters, original_sentences[i+1]):
            processed_sentences.append((original_sentences[i] + original_sentences[i+1]).strip())
            i += 2
        else:
            if original_sentences[i].strip():
                processed_sentences.append(original_sentences[i].strip())
            i += 1
    
    original_segments = re.split(f'({segment_delimiters})', original_text)
    processed_segments = []
    i = 0
    while i < len(original_segments):
        if i + 1 < len(original_segments) and re.match(segment_delimiters, original_segments[i+1]):
            processed_segments.append((original_segments[i] + original_segments[i+1]).strip())
            i += 2
        else:
            if original_segments[i].strip():
                processed_segments.append(original_segments[i].strip())
            i += 1
    
    processed_segments = [seg.strip() for seg in processed_segments if len(clean_text_for_comparison(seg)) > 2]
    
    # 建立短句到长句的映射
    segment_to_sentence = {}
    for segment in processed_segments:
        clean_segment = clean_text_for_comparison(segment)
        best_match = None
        best_score = -1
        
        for sentence in processed_sentences:
            clean_sentence = clean_text_for_comparison(sentence)
            if clean_segment in clean_sentence:
                coverage = len(clean_segment) / len(clean_sentence)
                score = len(clean_segment) * (1 + coverage)
                if score > best_score:
                    best_score = score
                    best_match = sentence
        
        if best_match:
            segment_to_sentence[segment] = best_match
    
    # 处理每个字幕条目
    sentence_mappings = []
    subtitle_corrections = {}
    
    for subtitle in subtitles:
        subtitle_text = subtitle['text'].strip()
        subtitle_number = subtitle['number']
        if not subtitle_text:
            continue
        
        clean_subtitle = clean_text_for_comparison(subtitle_text)
        
        # 寻找最佳匹配的原文短句
        best_match_segment = None
        best_score = -1
        
        for original_segment in processed_segments:
            clean_original = clean_text_for_comparison(original_segment)
            if not clean_original:
                continue
            
            similarity = difflib.SequenceMatcher(None, clean_subtitle, clean_original).ratio()
            len_ratio = len(clean_original) / len(clean_subtitle) if len(clean_subtitle) > 0 else 0
            common_chars = sum(1 for c in clean_subtitle if c in clean_original)
            char_ratio = common_chars / len(clean_subtitle) if len(clean_subtitle) > 0 else 0
            
            score = (similarity * 0.4 + char_ratio * 0.4 + (1 - abs(1 - len_ratio)) * 0.2) * len(clean_subtitle)
            
            if score > best_score:
                best_score = score
                best_match_segment = original_segment
        
        if not best_match_segment:
            best_match_segment = min(processed_segments, 
                                   key=lambda x: abs(len(clean_text_for_comparison(x)) - len(clean_subtitle)) 
                                   if len(clean_text_for_comparison(x)) > 0 else float('inf'))
        
        # 尝试多短句组合以提高匹配度
        improved_segment, improved_similarity = find_best_multi_segment_combination(
            processed_segments, best_match_segment, subtitle_text)
        
        if improved_similarity > 0:
            best_match_segment = improved_segment
        
        # 找到对应的原文长句
        original_sentence = segment_to_sentence.get(best_match_segment)
        if not original_sentence:
            for sentence in processed_sentences:
                if clean_text_for_comparison(best_match_segment) in clean_text_for_comparison(sentence):
                    original_sentence = sentence
                    break
        
        # 如果多短句组合后找不到对应长句，使用包含最多字符的长句
        if not original_sentence:
            clean_best_match = clean_text_for_comparison(best_match_segment)
            best_sentence_match = None
            best_overlap = 0
            
            for sentence in processed_sentences:
                clean_sentence = clean_text_for_comparison(sentence)
                overlap = len(set(clean_best_match) & set(clean_sentence))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_sentence_match = sentence
            
            if best_sentence_match:
                original_sentence = best_sentence_match
        
        if original_sentence:
            prev_sentence, next_sentence = find_context_sentences(original_text, best_match_segment, original_sentence)
            
            clean_best_match = clean_text_for_comparison(best_match_segment)
            char_diff = len(clean_subtitle) - len(clean_best_match)
            similarity = difflib.SequenceMatcher(None, clean_subtitle, clean_best_match).ratio()
            
            # 获取原文长句中的短句集合
            sentence_segments = []
            current_segment = ""
            delimiters = '，；：、,.;:！？。!?."\'""''「」『』【】《》〈〉—–-…～'
            
            i = 0
            while i < len(original_sentence):
                char = original_sentence[i]
                current_segment += char
                
                # 检查下一个字符是否是分隔符
                if i + 1 < len(original_sentence) and original_sentence[i + 1] in delimiters:
                    current_segment += original_sentence[i + 1]  # 添加分隔符
                    sentence_segments.append(current_segment.strip())
                    current_segment = ""
                    i += 2  # 跳过当前字符和分隔符
                else:
                    i += 1
            
            # 添加最后一段（如果有的话）
            if current_segment.strip():
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
                'sentence_segments': '|'.join(sentence_segments),  # 用|分割的短句集合
                'combined_prev_segment': prev_sentence + best_match_segment if prev_sentence != "null" else best_match_segment,
                'combined_next_segment': best_match_segment + next_sentence if next_sentence != "null" else best_match_segment
            }
            
            # 计算组合文本的相似度
            for key, combined_text in [('combined_similarity', mapping_info['combined_prev_segment']),
                                     ('combined_next_similarity', mapping_info['combined_next_segment'])]:
                if combined_text != "null" and subtitle_text:
                    clean_combined = clean_text_for_comparison(combined_text)
                    clean_subtitle = clean_text_for_comparison(subtitle_text)
                    combined_similarity = difflib.SequenceMatcher(None, clean_combined, clean_subtitle).ratio()
                    mapping_info[key] = combined_similarity
                else:
                    mapping_info[key] = 0.0
            
            sentence_mappings.append(mapping_info)
            
            # 选择最佳版本进行更正
            if corrected_srt_path:
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
    
    # 写入映射文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("字幕行号\t字幕\t原文短句\t字符差值\t相似度\t原文长句\t前一句\t后一句\t短句集合\t前一句+原文短句\t原文短句+后一句\n")
        for mapping in sentence_mappings:
            f.write(f"{mapping['subtitle_number']}\t{mapping['subtitle_text']}\t{mapping['original_segment']}\t"
                   f"{mapping['char_diff']}\t{mapping['similarity']:.2f}\t{mapping['original_sentence']}\t"
                   f"{mapping['prev_sentence']}\t{mapping['next_sentence']}\t{mapping['sentence_segments']}\t"
                   f"{mapping['combined_prev_segment']}\t{mapping['combined_next_segment']}\n")
    
    print(f"映射文件已生成：{output_path}")
    
    # 生成最终修正映射文件
    corrected_mapping_path = os.path.join(os.path.dirname(output_path), 
                                        os.path.splitext(os.path.basename(output_path))[0] + "_final.txt")
    
    with open(corrected_mapping_path, 'w', encoding='utf-8') as f:
        f.write("字幕行号\t字幕\t修正文本\t使用类型\t原相似度\t修正后相似度\n")
        for mapping in sentence_mappings:
            original_similarity = mapping['similarity']
            prev_similarity = mapping['combined_similarity']
            next_similarity = mapping['combined_next_similarity']
            
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
            
            f.write(f"{mapping['subtitle_number']}\t{mapping['subtitle_text']}\t{corrected_text}\t{use_type}\t"
                   f"{original_similarity:.2f}\t{final_similarity:.2f}\n")
    
    print(f"最终修正映射文件已生成：{corrected_mapping_path}")
    
    # 分析字符差值较大的映射
    print_large_char_diff_mappings(sentence_mappings)
    
    # 生成更正后的字幕文件
    if corrected_srt_path and subtitle_corrections:
        corrected_subtitles = []
        for subtitle in subtitles:
            corrected_text = subtitle_corrections.get(subtitle['number'], subtitle['text'])
            corrected_subtitles.append({
                'number': subtitle['number'],
                'timestamp': subtitle['timestamp'],
                'text': corrected_text
            })
        
        with open(corrected_srt_path, 'w', encoding='utf-8') as f:
            for subtitle in corrected_subtitles:
                f.write(f"{subtitle['number']}\n")
                f.write(f"{subtitle['timestamp']}\n")
                f.write(f"{subtitle['text']}\n\n")
        
        print(f"更正后的字幕文件已生成：{corrected_srt_path}")
    
    return sentence_mappings

def correct_srt_with_mapping(original_text_path, srt_path, output_path):
    """使用字符映射文件纠正SRT字幕"""
    srt_dir = os.path.dirname(srt_path)
    srt_name = os.path.splitext(os.path.basename(srt_path))[0]
    mapping_file_path = os.path.join(srt_dir, f"{srt_name}_mapping.txt")
    
    generate_character_mapping(original_text_path, srt_path, mapping_file_path)
    mapping_dict = load_character_mapping(mapping_file_path)
    
    subtitles = parse_srt(srt_path)
    corrected_subtitles = []
    corrected_count = 0
    
    for subtitle in subtitles:
        corrected_text = apply_character_mapping(subtitle['text'], mapping_dict)
        if corrected_text != subtitle['text']:
            corrected_count += 1
        
        corrected_subtitles.append({
            'number': subtitle['number'],
            'timestamp': subtitle['timestamp'],
            'text': corrected_text
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for subtitle in corrected_subtitles:
            f.write(f"{subtitle['number']}\n")
            f.write(f"{subtitle['timestamp']}\n")
            f.write(f"{subtitle['text']}\n\n")
    
    print(f"纠错完成！输出文件：{output_path}")
    print(f"总字幕条数：{len(corrected_subtitles)}")
    print(f"纠正条数：{corrected_count}")
    
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
    
    if args.output:
        output_file = args.output
    else:
        srt_dir = os.path.dirname(args.srt_file)
        srt_name = os.path.splitext(os.path.basename(args.srt_file))[0]
        output_file = os.path.join(srt_dir, f"{srt_name}_corrected.srt")
    
    if not os.path.exists(args.srt_file):
        print(f"错误：SRT字幕文件不存在：{args.srt_file}")
        sys.exit(1)
    
    # 如果指定了映射文件，则使用映射文件进行更正
    if args.char_mapping:
        if not os.path.exists(args.char_mapping):
            print(f"错误：字符映射文件不存在：{args.char_mapping}")
            sys.exit(1)
        
        mapping_dict = load_character_mapping(args.char_mapping)
        subtitles = parse_srt(args.srt_file)
        
        corrected_subtitles = []
        for subtitle in subtitles:
            corrected_text = apply_character_mapping(subtitle['text'], mapping_dict).strip()
            corrected_subtitles.append({
                'number': subtitle['number'],
                'timestamp': subtitle['timestamp'],
                'text': corrected_text
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for subtitle in corrected_subtitles:
                f.write(f"{subtitle['number']}\n")
                f.write(f"{subtitle['timestamp']}\n")
                f.write(f"{subtitle['text'].strip()}\n\n")
        
        print(f"输出文件：{output_file}")
        return
    
    # 如果提供了原始文本，则生成映射并更正
    if args.original_text:
        if not os.path.exists(args.original_text):
            print(f"错误：原始文本文件不存在：{args.original_text}")
            sys.exit(1)
        
        srt_dir = os.path.dirname(args.srt_file)
        srt_name = os.path.splitext(os.path.basename(args.srt_file))[0]
        sentence_mapping_file = os.path.join(srt_dir, f"{srt_name}_sentence_mapping.txt")
        
        if args.generate_only:
            generate_sentence_mapping(args.original_text, args.srt_file, sentence_mapping_file)
        else:
            generate_sentence_mapping(args.original_text, args.srt_file, sentence_mapping_file, output_file)
        
        return
    
    print("错误：请指定映射文件或提供原始文本文件")
    sys.exit(1)

if __name__ == "__main__":
    main()