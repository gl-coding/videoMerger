#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将SRT字幕转换为ASS字幕，并为字幕添加复杂特效。
支持通过--align参数指定字幕对齐方式，--font参数指定字体，--size参数指定字体大小，--color参数指定字体颜色。
支持通过--effect参数指定单一动画效果，或通过--effects参数指定多个动画效果（用逗号分隔，如"fade,move,scale"）进行轮播。
支持通过--highlight参数启用关键词高亮功能，使用NLP技术自动识别重要词语并突出显示。
支持通过--keyword-size参数指定关键词的字体大小（默认比普通文字大20%）。
支持通过--per-line参数启用逐行关键词分析（每行字幕提取最重要的词）。
支持通过--dict-file参数指定补充词典文件，文件中每行一个词，这些词会作为NLP分析的补充被高亮显示。
支持通过--skip-lines参数指定要跳过分析的字幕行号（从1开始），多个行号用逗号分隔。
支持通过--effect typewriter参数实现单字逐个显示的打字机效果。
支持通过--max-chars参数指定每行最大字符数，超过时自动换行。
用法：python3 srt2ass_with_effect.py input.srt output.ass [--align 5] [--font "行书"] [--size 100] [--color white] [--effects "fade,move,scale,typewriter"] [--highlight] [--keyword-size 120] [--per-line] [--dict-file words.txt] [--skip-lines "1,3,5"] [--max-chars 20]
"""
import sys
import os
import srt
import re
from datetime import timedelta
import argparse
import math
import jieba
import jieba.analyse
from collections import defaultdict

# 预定义的颜色（BGR格式）
COLORS = {
    "white": "&H00FFFFFF",    # 白色
    "yellow": "&H0000FFFF",   # 黄色
    "red": "&H000000FF",      # 红色
    "blue": "&H00FF0000",     # 蓝色
    "green": "&H0000FF00",    # 绿色
    "pink": "&H00FF00FF",     # 粉色
    "cyan": "&H00FFFF00",     # 青色
    "black": "&H00000000",    # 黑色
    "orange": "&H000080FF",   # 橙色
    "purple": "&H00FF0080",   # 紫色
}

# 高亮颜色配置（按重要性排序）
HIGHLIGHT_COLORS = [
    COLORS["red"],      # 最重要
    COLORS["yellow"],   # 次重要
]

# 视频分辨率
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

def get_center_pos():
    """获取屏幕中心坐标"""
    return VIDEO_WIDTH // 2, VIDEO_HEIGHT // 2

# 预定义的动画效果
EFFECTS = {
    "fade": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\fade(255,0,255,0,500,{duration_ms-500},{duration_ms})\\bord3\\shad2}}"
    ),
    "move_right": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\move({VIDEO_WIDTH//4},{VIDEO_HEIGHT//2},{VIDEO_WIDTH*3//4},{VIDEO_HEIGHT//2})\\bord3\\shad2}}"
    ),
    "move_left": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\move({VIDEO_WIDTH*3//4},{VIDEO_HEIGHT//2},{VIDEO_WIDTH//4},{VIDEO_HEIGHT//2})\\bord3\\shad2}}"
    ),
    "move_up": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\move({VIDEO_WIDTH//2},{VIDEO_HEIGHT*3//4},{VIDEO_WIDTH//2},{VIDEO_HEIGHT//4})\\bord3\\shad2}}"
    ),
    "move_down": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\move({VIDEO_WIDTH//2},{VIDEO_HEIGHT//4},{VIDEO_WIDTH//2},{VIDEO_HEIGHT*3//4})\\bord3\\shad2}}"
    ),
    "zoom": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\t(0,{duration_ms},\\fscx120\\fscy120)\\bord3\\shad2}}"
    ),
    "rotate": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\org({VIDEO_WIDTH//2},{VIDEO_HEIGHT//2})\\t(0,{duration_ms},\\frz360)\\bord3\\shad2}}"
    ),
    "shake": lambda duration_ms, align_tag: (
        # 使用\pos设置初始位置，然后用\t和\frx实现快速抖动
        f"{{{align_tag}\\pos({VIDEO_WIDTH//2},{VIDEO_HEIGHT//2})"
        f"\\t(0,{duration_ms//16},\\frx8)\\t({duration_ms//16},{duration_ms//8},\\frx-8)"
        f"\\t({duration_ms//8},{duration_ms*3//16},\\frx8)\\t({duration_ms*3//16},{duration_ms//4},\\frx-8)"
        f"\\t({duration_ms//4},{duration_ms*5//16},\\frx8)\\t({duration_ms*5//16},{duration_ms*3//8},\\frx-8)"
        f"\\t({duration_ms*3//8},{duration_ms*7//16},\\frx8)\\t({duration_ms*7//16},{duration_ms//2},\\frx-8)"
        f"\\t({duration_ms//2},{duration_ms*9//16},\\frx8)\\t({duration_ms*9//16},{duration_ms*5//8},\\frx-8)"
        f"\\t({duration_ms*5//8},{duration_ms*11//16},\\frx8)\\t({duration_ms*11//16},{duration_ms*3//4},\\frx-8)"
        f"\\t({duration_ms*3//4},{duration_ms*13//16},\\frx8)\\t({duration_ms*13//16},{duration_ms*7//8},\\frx-8)"
        f"\\t({duration_ms*7//8},{duration_ms*15//16},\\frx8)\\t({duration_ms*15//16},{duration_ms},\\frx0)\\bord3\\shad2}}"
    ),
    "wave": lambda duration_ms, align_tag: (
        # 使用更快的波浪效果，增加旋转角度
        f"{{{align_tag}\\pos({VIDEO_WIDTH//2},{VIDEO_HEIGHT//2})"
        f"\\t(0,{duration_ms//8},\\frz8)\\t({duration_ms//8},{duration_ms//4},\\frz-8)"
        f"\\t({duration_ms//4},{duration_ms*3//8},\\frz8)\\t({duration_ms*3//8},{duration_ms//2},\\frz-8)"
        f"\\t({duration_ms//2},{duration_ms*5//8},\\frz8)\\t({duration_ms*5//8},{duration_ms*3//4},\\frz-8)"
        f"\\t({duration_ms*3//4},{duration_ms*7//8},\\frz8)\\t({duration_ms*7//8},{duration_ms},\\frz0)\\bord3\\shad2}}"
    ),
    "bounce": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\move({VIDEO_WIDTH//2},{VIDEO_HEIGHT//2-50},{VIDEO_WIDTH//2},{VIDEO_HEIGHT//2},0.5,1)\\bord3\\shad2}}"
    ),
    "typewriter": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\bord3\\shad2}}"
    ),
    "none": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\bord3\\shad2}}"
    ),
}

def srt_time_to_ass(ts: timedelta) -> str:
    total_seconds = int(ts.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    centiseconds = int(ts.microseconds / 10000)
    return f"{hours:01d}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

def generate_ass_header(font_name="行书", font_size=100, primary_color="&H00FFFFFF", outline_color="&H00000000", shadow_color="&H80000000", alignment=5):
    # Alignment: 1=左下, 2=中下, 3=右下, 4=左中, 5=正中, 6=右中, 7=左上, 8=中上, 9=右上
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {VIDEO_WIDTH}
PlayResY: {VIDEO_HEIGHT}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},{shadow_color},-1,0,0,0,100,100,0,0,1,3,2,{alignment},30,30,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def analyze_keywords(text, top_k=3, min_word_len=2):
    """
    使用TextRank算法分析文本中的关键词
    Args:
        text: 要分析的文本
        top_k: 提取前k个关键词
        min_word_len: 最小词长度，小于此长度的词将被忽略
    返回: 关键词列表及其权重
    """
    if not text or len(text.strip()) < min_word_len:
        return []
        
    # 使用jieba分词获取所有词
    words = list(jieba.cut(text, cut_all=False))
    # 过滤掉太短的词和停用词
    valid_words = [w for w in words if len(w) >= min_word_len and not w.isspace()]
    
    if not valid_words:
        return []
    
    try:
        # 首先尝试使用TextRank算法
        keywords = jieba.analyse.textrank(text, topK=top_k, withWeight=True)
        # 过滤掉太短的词
        keywords = [(word, weight) for word, weight in keywords if len(word) >= min_word_len]
        
        # 如果TextRank没有找到关键词，选择最长的词作为关键词
        if not keywords and valid_words:
            # 按词长度排序
            longest_word = max(valid_words, key=len)
            keywords = [(longest_word, 0.5)]  # 使用0.5作为默认权重
            
        return keywords
    except Exception as e:
        print(f"警告：分析文本时出错：{e}")
        # 发生错误时，选择最长的词作为关键词
        if valid_words:
            longest_word = max(valid_words, key=len)
            return [(longest_word, 0.5)]
        return []

def find_longest_word(text, min_word_len=2):
    """
    找出文本中最长的词
    """
    if not text:
        return None, 0
    
    words = list(jieba.cut(text, cut_all=False))
    valid_words = [w for w in words if len(w) >= min_word_len and not w.isspace()]
    
    if not valid_words:
        return None, 0
        
    longest_word = max(valid_words, key=len)
    return longest_word, 0.5  # 使用0.5作为默认权重

def load_custom_dictionary(dict_file):
    """
    从文件加载自定义词典
    返回: 词典中的词及其权重的字典（权重统一设为0.8表示重要性较高）
    """
    keywords_dict = {}
    try:
        with open(dict_file, 'r', encoding='utf-8') as f:
            words = f.readlines()
        # 去除空行和空白字符，并将权重统一设为0.8
        keywords_dict = {word.strip(): 0.8 for word in words if word.strip()}
        print(f"已从词典文件加载 {len(keywords_dict)} 个词")
        return keywords_dict
    except Exception as e:
        print(f"警告：加载词典文件时出错：{e}")
        return {}

def merge_keywords(nlp_keywords, dict_keywords):
    """
    合并NLP分析出的关键词和词典中的关键词
    Args:
        nlp_keywords: NLP分析得到的关键词字典 {word: weight}
        dict_keywords: 词典中的关键词字典 {word: weight}
    Returns:
        合并后的关键词字典
    """
    # 创建一个新字典来存储合并结果
    merged = nlp_keywords.copy()
    
    # 将词典中的词添加到结果中（如果已存在则保留较高的权重）
    for word, weight in dict_keywords.items():
        if word not in merged or merged[word] < weight:
            merged[word] = weight
            
    return merged

def process_subtitle_text(text, keywords_dict, base_size, keyword_size):
    """
    处理字幕文本，为关键词添加颜色和大小标记
    """
    if not text:
        return text
        
    # 使用jieba分词
    words = jieba.cut(text, cut_all=False)
    words = list(words)
    
    # 为每个词分配样式
    word_styles = []
    for word in words:
        if word in keywords_dict:
            # 根据关键词权重选择颜色
            weight = keywords_dict[word]
            # 将权重归一化到[0,1]区间，然后用于选择颜色
            color_index = 1 if weight < 0.5 else 0  # 权重高用红色，低用黄色
            word_styles.append((word, HIGHLIGHT_COLORS[color_index], keyword_size))
        else:
            word_styles.append((word, COLORS["white"], base_size))
    
    # 构建带样式的文本
    result = ""
    for word, color, size in word_styles:
        result += f"{{\\c{color}\\fs{size}}}{word}"
    
    return result

def apply_dual_style(content, primary_color, secondary_color, primary_size, secondary_size, split_pos):
    """应用双重样式（颜色和大小）到文本"""
    if split_pos <= 0 or split_pos >= len(content):
        return f"{{\\c{primary_color}\\fs{primary_size}}}{content}"
    
    first_part = content[:split_pos]
    second_part = content[split_pos:]
    return f"{{\\c{primary_color}\\fs{primary_size}}}{first_part}{{\\c{secondary_color}\\fs{secondary_size}}}{second_part}"

def apply_typewriter_effect(text, duration_ms):
    """为文本应用打字机效果，每个字符逐个显示"""
    if not text:
        return text
        
    # 移除现有的样式标签以便处理纯文本
    # 先保存样式信息
    style_match = re.match(r'^({\\c[^}]*\\fs\d+})(.*)', text)
    style_tag = ""
    content = text
    
    if style_match:
        style_tag = style_match.group(1)
        content = style_match.group(2)
    
    # 计算每个字符的延迟时间
    char_count = len(content)
    if char_count <= 1:
        return text
        
    # 每个字符显示的时间间隔
    interval = duration_ms / (char_count * 1.2)  # 留一些时间让最后的字符可见
    
    result = ""
    current_time = 0
    
    # 特殊处理换行符\N
    segments = []
    current_segment = ""
    i = 0
    while i < len(content):
        # 检查是否是\N换行符
        if i < len(content) - 1 and content[i] == '\\' and content[i+1] == 'N':
            if current_segment:
                segments.append(current_segment)
            segments.append("\\N")  # 保留\N作为一个整体
            current_segment = ""
            i += 2  # 跳过\N两个字符
        else:
            current_segment += content[i]
            i += 1
    
    # 添加最后一个片段
    if current_segment:
        segments.append(current_segment)
    
    # 为每个字符添加延迟显示标签，但\N作为一个整体处理
    for segment in segments:
        if segment == "\\N":
            # 换行符直接添加，不添加动画效果
            result += "\\N"
        else:
            # 正常字符逐个添加动画效果
            for char in segment:
                result += f"{style_tag}{{\\alpha&HFF&\\t({int(current_time)},{int(current_time+10)},\\alpha&H00&)}}{char}"
                current_time += interval
    
    return result

def wrap_text_by_char_count(text, max_chars):
    """
    按照最大字符数对文本进行换行处理
    Args:
        text: 原始文本
        max_chars: 每行最大字符数
    返回: 处理后的文本
    """
    if not text or max_chars <= 0:
        return text
        
    result = []
    current_line = ""
    
    # 处理可能已经包含\N的情况
    lines = text.split('\\N')
    
    for line in lines:
        if not line:
            result.append("")
            continue
            
        # 如果当前行已经小于最大字符数，直接添加
        if len(line) <= max_chars:
            result.append(line)
            continue
            
        # 需要进一步分割的情况
        chars = list(line)
        current_line = ""
        
        for char in chars:
            if len(current_line) >= max_chars:
                result.append(current_line)
                current_line = char
            else:
                current_line += char
                
        # 添加最后一行
        if current_line:
            result.append(current_line)
    
    return '\\N'.join(result)

def srt2ass(srt_path, ass_path, font_size=100, font_name="行书", alignment=5, color="white", 
            effect="fade", effects=None, color2=None, size2=None, split_pos=0, highlight=False, 
            keyword_size=None, per_line=False, dict_file=None, skip_lines=None, max_chars=0):
    """
    转换SRT到ASS，支持关键词高亮和动画效果轮播
    """
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    subs = list(srt.parse(srt_content))
    
    # 解析动画效果列表
    effect_list = []
    if effects:
        # 解析多个效果
        for e in effects.split(','):
            e = e.strip().lower()
            if e in EFFECTS:
                effect_list.append(e)
            else:
                print(f"警告：未知的动画效果 '{e}'，将被忽略")
        if not effect_list:
            print(f"警告：没有有效的动画效果，将使用默认效果 '{effect}'")
            effect_list = [effect]
    else:
        # 使用单一效果
        effect_list = [effect]
    
    print(f"\n动画效果轮播顺序：{' → '.join(effect_list)}")
    
    # 解析要跳过的行号
    skip_lines_set = set()
    if skip_lines:
        try:
            skip_lines_set = {int(x.strip()) for x in skip_lines.split(',')}
            print(f"\n将跳过以下行号的分析：{sorted(skip_lines_set)}")
        except ValueError as e:
            print(f"警告：行号解析失败 ({e})，将不跳过任何行")
            skip_lines_set = set()
    
    # 加载自定义词典（如果指定）
    dict_keywords = {}
    if dict_file:
        dict_keywords = load_custom_dictionary(dict_file)
        print(f"\n已从词典文件加载 {len(dict_keywords)} 个补充词")
    
    # 如果启用高亮，预处理字幕文本以提取关键词
    keywords_dict = {}
    if highlight:
        if per_line:
            print("逐行分析关键词：")
            # 每行字幕单独分析，提取关键词
            for i, sub in enumerate(subs, 1):  # 从1开始计数，与SRT文件行号对应
                # 如果当前行需要跳过分析
                if i in skip_lines_set:
                    print(f"  跳过第{i}行：{sub.content.replace(chr(10), ' ')}")
                    continue
                
                # NLP分析
                line_keywords = analyze_keywords(sub.content, top_k=1, min_word_len=2)
                nlp_dict = {}
                if line_keywords:
                    word, weight = line_keywords[0]
                    nlp_dict[word] = weight
                else:
                    # 如果没有找到关键词，使用最长的词
                    word, weight = find_longest_word(sub.content)
                    if word:
                        nlp_dict[word] = weight
                
                # 合并NLP结果和词典词
                line_dict = merge_keywords(nlp_dict, dict_keywords)
                
                # 更新全局关键词字典
                keywords_dict.update(line_dict)
                
                # 打印分析结果
                print(f"  第{i}行：{sub.content.replace(chr(10), ' ')}")
                for word, weight in line_dict.items():
                    source = "NLP分析" if word in nlp_dict else "词典补充"
                    color = "红色" if weight >= 0.5 else "黄色"
                    print(f"  关键词：{word} ({color}, 权重: {weight:.4f}) [{source}]")
                print()
        else:
            # 合并所有非跳过行的字幕文本进行整体分析
            all_text = ' '.join(sub.content for i, sub in enumerate(subs, 1) 
                              if i not in skip_lines_set)
            nlp_keywords = analyze_keywords(all_text, top_k=5, min_word_len=2)  # 提取前5个关键词
            nlp_dict = {word: weight for word, weight in nlp_keywords}
            
            # 合并NLP结果和词典词
            keywords_dict = merge_keywords(nlp_dict, dict_keywords)
            
            # 打印分析结果
            print("关键词分析结果：")
            if skip_lines_set:
                print(f"（已跳过第 {', '.join(map(str, sorted(skip_lines_set)))} 行的分析）")
            for word, weight in keywords_dict.items():
                source = "NLP分析" if word in nlp_dict else "词典补充"
                color = "红色" if weight >= 0.5 else "黄色"
                print(f"  {word}: {weight:.4f} ({color}) [{source}]")
    
    # 设置关键词字体大小
    if keyword_size is None:
        keyword_size = int(font_size * 1.2)  # 默认比普通字体大20%
    
    # 获取颜色代码
    primary_color = COLORS.get(color.lower(), COLORS["white"])
    secondary_color = COLORS.get(color2.lower(), primary_color) if color2 else primary_color
    
    ass_lines = [generate_ass_header(
        font_name=font_name,
        font_size=font_size,
        primary_color=primary_color,
        alignment=alignment
    )]
    
    for i, sub in enumerate(subs, 1):
        start = srt_time_to_ass(sub.start)
        end = srt_time_to_ass(sub.end)
        duration_ms = int((sub.end - sub.start).total_seconds() * 1000)
        
        # 替换文本中的换行符
        content = sub.content.replace('\n', '\\N')
        
        # 如果指定了最大字符数，进行自动换行处理
        if max_chars > 0:
            content = wrap_text_by_char_count(content, max_chars)
        
        # 处理文本样式
        if highlight:
            # 如果是跳过的行，使用普通样式
            if i in skip_lines_set:
                content = f"{{\\c{primary_color}\\fs{font_size}}}{content}"
            else:
                # 使用NLP处理添加关键词高亮
                content = process_subtitle_text(content, keywords_dict, font_size, keyword_size)
        elif (color2 or size2) and split_pos > 0:
            # 使用传统的双重样式
            content = apply_dual_style(content, primary_color, secondary_color, font_size, size2, split_pos)
        else:
            # 使用单一样式
            content = f"{{\\c{primary_color}\\fs{font_size}}}{content}"
        
        # 获取当前行的动画效果（轮播）
        current_effect = effect_list[(i - 1) % len(effect_list)]
        effect_func = EFFECTS[current_effect]
        
        # 强制加\anX对齐标签和动画效果
        effect_tag = effect_func(duration_ms, f"\\an{alignment}")
        
        # 如果是打字机效果，应用特殊处理
        if current_effect == "typewriter":
            content = apply_typewriter_effect(content, duration_ms)
        
        # 移除可能重复的花括号
        effect_tag = effect_tag.rstrip('}')
        if not current_effect == "typewriter":  # 打字机效果已经处理过内容，不需要再处理
            content = content.lstrip('{')
        
        # 组合所有标签和内容
        text = effect_tag + content
        dialogue = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
        ass_lines.append(dialogue)
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ass_lines))
    print(f"\n转换完成: {ass_path}")
    if highlight:
        mode = "逐行分析" if per_line else "整体分析"
        sources = []
        if dict_file:
            sources.append("词典补充")
        sources.append("NLP分析")
        print(f"已启用关键词高亮功能（{mode} + {' + '.join(sources)}）")
        if skip_lines_set:
            print(f"已跳过第 {', '.join(map(str, sorted(skip_lines_set)))} 行的分析")
        print(f"普通文字大小: {font_size}")
        print(f"关键词大小: {keyword_size}")
    else:
        print(f"使用字体: {font_name}, 大小1: {font_size}, 大小2: {size2}, "
              f"颜色1: {color}, 颜色2: {color2}, 分割位置: {split_pos}, "
              f"对齐: {alignment}")
        if effects:
            print(f"动画效果轮播：{' → '.join(effect_list)}")
        else:
            print(f"动画效果：{effect}")
    
    if max_chars > 0:
        print(f"已启用自动换行，每行最大字符数: {max_chars}")

def main():
    parser = argparse.ArgumentParser(description='将SRT字幕转换为ASS字幕，并添加特效')
    parser.add_argument('input', help='输入的SRT文件路径')
    parser.add_argument('output', help='输出的ASS文件路径')
    parser.add_argument('--font', default='行书', help='字体名称')
    parser.add_argument('--size', type=int, default=100, help='字体大小')
    parser.add_argument('--align', type=int, choices=range(1,10), default=5, help='对齐方式(1-9)')
    parser.add_argument('--color', default='white', help='字体颜色')
    parser.add_argument('--effect', default='fade', help='单一动画效果(包括typewriter打字机效果)')
    parser.add_argument('--effects', help='多个动画效果，用逗号分隔（如"fade,move,typewriter"）')
    parser.add_argument('--color2', help='第二种颜色（用于双重样式）')
    parser.add_argument('--size2', type=int, help='第二种字体大小（用于双重样式）')
    parser.add_argument('--split', type=int, default=0, help='颜色分割位置（用于双重样式）')
    parser.add_argument('--highlight', action='store_true', help='启用关键词高亮')
    parser.add_argument('--keyword-size', type=int, help='关键词字体大小')
    parser.add_argument('--per-line', action='store_true', help='逐行分析关键词')
    parser.add_argument('--dict-file', help='补充词典文件路径')
    parser.add_argument('--skip-lines', help='要跳过分析的行号列表，用逗号分隔（如"1,3,5"）')
    parser.add_argument('--max-chars', type=int, default=0, help='每行最大字符数，超过时自动换行（0表示不限制）')
    
    args = parser.parse_args()
    
    srt2ass(
        args.input, args.output,
        font_size=args.size,
        font_name=args.font,
        alignment=args.align,
        color=args.color,
        effect=args.effect,
        effects=args.effects,
        color2=args.color2,
        size2=args.size2,
        split_pos=args.split,
        highlight=args.highlight,
        keyword_size=args.keyword_size,
        per_line=args.per_line,
        dict_file=args.dict_file,
        skip_lines=args.skip_lines,
        max_chars=args.max_chars
    )

if __name__ == "__main__":
    main() 