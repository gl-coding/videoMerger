#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并SRT字幕文件中内容相同的相邻字幕条目。
将相邻且内容相同的字幕的时间戳合并为一个更长的时间段。

用法：python3 merge_duplicate_subtitles.py input.srt output.srt
"""

import sys
import re
import os
from datetime import timedelta

def parse_time(time_str):
    """解析SRT时间戳为时、分、秒、毫秒"""
    pattern = r'(\d+):(\d+):(\d+),(\d+)'
    match = re.match(pattern, time_str)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        milliseconds = int(match.group(4))
        return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
    return None

def format_time(td):
    """将timedelta格式化为SRT时间戳格式"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def parse_srt(file_path):
    """解析SRT文件，返回字幕条目列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分割为字幕块
    subtitle_blocks = re.split(r'\n\s*\n', content.strip())
    subtitles = []
    
    for block in subtitle_blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:  # 至少需要序号、时间戳和内容
            index = int(lines[0])
            time_line = lines[1]
            text = '\n'.join(lines[2:])
            
            # 解析时间戳
            time_match = re.match(r'(\d+:\d+:\d+,\d+)\s+-->\s+(\d+:\d+:\d+,\d+)', time_line)
            if time_match:
                start_time = parse_time(time_match.group(1))
                end_time = parse_time(time_match.group(2))
                
                subtitles.append({
                    'index': index,
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': text
                })
    
    return subtitles

def merge_duplicate_subtitles(subtitles):
    """合并内容相同的相邻字幕"""
    if not subtitles:
        return []
    
    merged = []
    current = subtitles[0]
    
    for i in range(1, len(subtitles)):
        next_sub = subtitles[i]
        
        # 如果当前字幕和下一个字幕内容相同
        if current['text'].strip() == next_sub['text'].strip():
            # 不再检查时间间隔，只要内容相同就合并
            # 更新结束时间为两者中较晚的时间
            current['end_time'] = max(current['end_time'], next_sub['end_time'])
            # 如果下一个字幕的开始时间更早，也更新开始时间
            current['start_time'] = min(current['start_time'], next_sub['start_time'])
        else:
            # 内容不同，添加当前字幕并移动到下一个
            merged.append(current)
            current = next_sub
    
    # 添加最后一个处理的字幕
    merged.append(current)
    
    # 重新编号
    for i, sub in enumerate(merged, 1):
        sub['index'] = i
    
    return merged

def write_srt(subtitles, output_path):
    """将字幕列表写入SRT文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, sub in enumerate(subtitles, 1):
            # 格式化时间戳
            start_time_str = format_time(sub['start_time'])
            end_time_str = format_time(sub['end_time'])
            
            # 写入字幕块
            f.write(f"{sub['index']}\n")
            f.write(f"{start_time_str} --> {end_time_str}\n")
            f.write(f"{sub['text']}\n\n")

def main():
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} input.srt output.srt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在")
        sys.exit(1)
    
    print(f"正在处理文件: {input_file}")
    
    # 解析SRT文件
    subtitles = parse_srt(input_file)
    original_count = len(subtitles)
    print(f"原始字幕条数: {original_count}")
    
    # 合并相同内容的相邻字幕
    merged_subtitles = merge_duplicate_subtitles(subtitles)
    merged_count = len(merged_subtitles)
    print(f"合并后字幕条数: {merged_count}")
    print(f"减少了 {original_count - merged_count} 条重复字幕")
    
    # 写入结果
    write_srt(merged_subtitles, output_file)
    print(f"已保存合并后的字幕到: {output_file}")

if __name__ == "__main__":
    main() 