#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将SRT字幕转换为ASS字幕，并为字幕添加复杂特效。
支持通过--align参数指定字幕对齐方式，--font参数指定字体，--size参数指定字体大小，--color参数指定字体颜色，--effect参数指定动画效果。
支持通过--color2参数指定第二种颜色，--size2参数指定第二部分文字大小，--split参数指定分割位置（例如：3表示前3个字符使用第一种颜色和大小）。
用法：python3 srt2ass_with_effect.py input.srt output.ass [--align 5] [--font "行书"] [--size 100] [--color white] [--effect fade] [--color2 red] [--size2 120] [--split 3]
"""
import sys
import os
import srt
from datetime import timedelta
import argparse
import math

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

def apply_dual_style(content, primary_color, secondary_color, primary_size, secondary_size, split_pos):
    """应用双重样式（颜色和大小）到文本"""
    if split_pos <= 0 or split_pos >= len(content):
        return f"{{\\c{primary_color}\\fs{primary_size}}}{content}"
    
    first_part = content[:split_pos]
    second_part = content[split_pos:]
    return f"{{\\c{primary_color}\\fs{primary_size}}}{first_part}{{\\c{secondary_color}\\fs{secondary_size}}}{second_part}"

def srt2ass(srt_path, ass_path, font_size=100, font_name="行书", alignment=5, color="white", effect="fade", color2=None, size2=None, split_pos=0):
    # 获取颜色代码
    primary_color = COLORS.get(color.lower(), COLORS["white"])
    secondary_color = COLORS.get(color2.lower(), primary_color) if color2 else primary_color
    
    # 获取字体大小
    secondary_size = size2 if size2 else font_size
    
    # 获取动画效果函数
    effect_func = EFFECTS.get(effect.lower(), EFFECTS["fade"])
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    subs = list(srt.parse(srt_content))
    
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
        
        # 处理颜色和字体大小效果
        if (color2 or size2) and split_pos > 0:
            content = apply_dual_style(content, primary_color, secondary_color, font_size, secondary_size, split_pos)
        else:
            content = f"{{\\c{primary_color}\\fs{font_size}}}{content}"
        
        # 强制加\anX对齐标签和动画效果
        # 注意：所有控制标签都放在文本最前面
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
    print(f"转换完成: {ass_path}")
    print(f"使用字体: {font_name}, 大小1: {font_size}, 大小2: {secondary_size}, 颜色1: {color}, 颜色2: {color2}, 分割位置: {split_pos}, 对齐: {alignment}, 特效: {effect}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SRT转ASS并添加特效")
    parser.add_argument('srt_path', help='输入SRT文件')
    parser.add_argument('ass_path', help='输出ASS文件')
    parser.add_argument('--align', type=int, default=5, choices=range(1,10), help='字幕对齐方式，1~9，默认5（正中间）')
    parser.add_argument('--font', type=str, default="行书", help='字幕字体，默认行书。常用：行书、楷体、KaiTi、KaiTi_GB2312、STKaiti、Microsoft YaHei')
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
    args = parser.parse_args()
    srt2ass(args.srt_path, args.ass_path, font_size=args.size, font_name=args.font, 
            alignment=args.align, color=args.color, effect=args.effect,
            color2=args.color2, size2=args.size2, split_pos=args.split) 