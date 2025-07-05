#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将SRT字幕转换为ASS字幕，并为字幕添加复杂特效。
支持通过--align参数指定字幕对齐方式，--font参数指定字体，--size参数指定字体大小，--color参数指定字体颜色，--effect参数指定动画效果。
支持通过--color2参数指定第二种颜色，--size2参数指定第二部分文字大小，--split参数指定分割位置。
支持通过--highlight参数启用关键词高亮功能，使用NLP技术自动识别重要词语并突出显示。
支持通过--keyword-size参数指定关键词的字体大小（默认比普通文字大20%）。
支持通过--per-line参数启用逐行关键词分析（每行字幕提取最重要的词）。
用法：python3 srt2ass_with_effect.py input.srt output.ass [--align 5] [--font "行书"] [--size 100] [--color white] [--effect fade] [--highlight] [--keyword-size 120] [--per-line]
"""
import sys
import os
import srt
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
    "none": lambda duration_ms, align_tag: (
        f"{{{align_tag}\\pos({VIDEO_WIDTH//2},{VIDEO_HEIGHT//2})\\bord3\\shad2}}"
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

def process_subtitle_text(text, keywords_dict, base_size, keyword_size):
    """
    处理字幕文本，为关键词添加颜色和大小标记
    """
    if not text:
        return text
        
    # 使用jieba分词
    words = jieba.cut(text, cut_all=False)
    words = list(words)
    
    # 如果没有找到关键词，选择最长的词
    if not any(word in keywords_dict for word in words):
        longest_word, weight = find_longest_word(text)
        if longest_word:
            keywords_dict[longest_word] = weight
    
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

def srt2ass(srt_path, ass_path, font_size=100, font_name="行书", alignment=5, color="white", 
            effect="fade", color2=None, size2=None, split_pos=0, highlight=False, 
            keyword_size=None, per_line=False):
    """
    转换SRT到ASS，支持关键词高亮
    """
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    subs = list(srt.parse(srt_content))
    
    # 如果启用高亮，预处理字幕文本以提取关键词
    keywords_dict = {}
    if highlight:
        if per_line:
            print("逐行分析关键词：")
            # 每行字幕单独分析，提取一个最重要的词
            for sub in subs:
                line_keywords = analyze_keywords(sub.content, top_k=1, min_word_len=2)
                if line_keywords:
                    word, weight = line_keywords[0]
                    keywords_dict[word] = weight
                    color = "红色" if weight >= 0.5 else "黄色"
                    print(f"  字幕：{sub.content.replace(chr(10), ' ')}")
                    print(f"  关键词：{word} ({color}, 权重: {weight:.4f})")
                else:
                    # 如果没有找到关键词，使用最长的词
                    word, weight = find_longest_word(sub.content)
                    if word:
                        keywords_dict[word] = weight
                        print(f"  字幕：{sub.content.replace(chr(10), ' ')}")
                        print(f"  关键词：{word} (黄色, 权重: {weight:.4f}) [最长词]")
                print()
        else:
            # 合并所有字幕文本进行整体分析
            all_text = ' '.join(sub.content for sub in subs)
            keywords = analyze_keywords(all_text, top_k=5, min_word_len=2)  # 提取前5个关键词
            keywords_dict = {word: weight for word, weight in keywords}
            print("整体分析关键词（红色为重要，黄色为次要）：")
            for word, weight in keywords:
                color = "红色" if weight >= 0.5 else "黄色"
                print(f"  {word}: {weight:.4f} ({color})")
    
    # 设置关键词字体大小
    if keyword_size is None:
        keyword_size = int(font_size * 1.2)  # 默认比普通字体大20%
    
    # 获取颜色代码
    primary_color = COLORS.get(color.lower(), COLORS["white"])
    secondary_color = COLORS.get(color2.lower(), primary_color) if color2 else primary_color
    
    # 获取字体大小
    secondary_size = size2 if size2 else font_size
    
    # 获取动画效果函数
    effect_func = EFFECTS.get(effect.lower(), EFFECTS["fade"])
    
    ass_lines = [generate_ass_header(
        font_name=font_name,
        font_size=font_size,
        primary_color=primary_color,
        alignment=alignment
    )]
    
    for sub in subs:
        start = srt_time_to_ass(sub.start)
        end = srt_time_to_ass(sub.end)
        duration_ms = int((sub.end - sub.start).total_seconds() * 1000)
        
        # 替换文本中的换行符
        content = sub.content.replace('\n', '\\N')
        
        # 处理文本样式
        if highlight:
            # 使用NLP处理添加关键词高亮
            content = process_subtitle_text(content, keywords_dict, font_size, keyword_size)
        elif (color2 or size2) and split_pos > 0:
            # 使用传统的双重样式
            content = apply_dual_style(content, primary_color, secondary_color, font_size, secondary_size, split_pos)
        else:
            # 使用单一样式
            content = f"{{\\c{primary_color}\\fs{font_size}}}{content}"
        
        # 强制加\anX对齐标签和动画效果
        effect_tag = effect_func(duration_ms, f"\\an{alignment}")
        
        # 移除可能重复的花括号
        effect_tag = effect_tag.rstrip('}')
        content = content.lstrip('{')
        
        # 组合所有标签和内容
        text = effect_tag + content
        dialogue = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
        ass_lines.append(dialogue)
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ass_lines))
    print(f"\n转换完成: {ass_path}")
    if highlight:
        print(f"已启用关键词高亮功能 ({'逐行分析' if per_line else '整体分析'})")
        print(f"普通文字大小: {font_size}")
        print(f"关键词大小: {keyword_size}")
    else:
        print(f"使用字体: {font_name}, 大小1: {font_size}, 大小2: {secondary_size}, "
              f"颜色1: {color}, 颜色2: {color2}, 分割位置: {split_pos}, "
              f"对齐: {alignment}, 特效: {effect}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SRT转ASS并添加特效")
    parser.add_argument('srt_path', help='输入SRT文件')
    parser.add_argument('ass_path', help='输出ASS文件')
    parser.add_argument('--align', type=int, default=5, choices=range(1,10), 
                      help='字幕对齐方式，1~9，默认5（正中间）')
    parser.add_argument('--font', type=str, default="行书", 
                      help='字幕字体，默认行书。常用：行书、楷体、KaiTi、KaiTi_GB2312、STKaiti、Microsoft YaHei')
    parser.add_argument('--size', type=int, default=100, help='字体大小，默认100')
    parser.add_argument('--color', type=str, default="white", choices=list(COLORS.keys()),
                      help='字体颜色，可选：' + ', '.join(COLORS.keys()) + '，默认white')
    parser.add_argument('--effect', type=str, default="fade", choices=list(EFFECTS.keys()),
                      help='动画效果，可选：' + ', '.join(EFFECTS.keys()) + '，默认fade')
    parser.add_argument('--color2', type=str, choices=list(COLORS.keys()),
                      help='第二种字体颜色，如果不指定则整行使用相同颜色')
    parser.add_argument('--size2', type=int,
                      help='第二部分文字的大小，如果不指定则使用与第一部分相同的大小')
    parser.add_argument('--split', type=int, default=0,
                      help='分割位置（第几个字符后改变样式），默认0表示不分割')
    parser.add_argument('--highlight', action='store_true',
                      help='启用关键词高亮功能，自动识别重要词语并使用不同颜色突出显示')
    parser.add_argument('--keyword-size', type=int,
                      help='关键词的字体大小，默认比普通文字大20%')
    parser.add_argument('--per-line', action='store_true',
                      help='启用逐行关键词分析，每行字幕提取一个最重要的词')
    
    args = parser.parse_args()
    srt2ass(args.srt_path, args.ass_path, font_size=args.size, font_name=args.font, 
            alignment=args.align, color=args.color, effect=args.effect,
            color2=args.color2, size2=args.size2, split_pos=args.split,
            highlight=args.highlight, keyword_size=args.keyword_size,
            per_line=args.per_line) 