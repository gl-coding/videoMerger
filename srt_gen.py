#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转字幕工具 - 使用Whisper将音频转换为SRT字幕文件
"""

import whisper
import os
import sys
from datetime import timedelta


def format_timestamp(seconds):
    """
    将秒数转换为SRT时间格式 (HH:MM:SS,mmm)
    
    Args:
        seconds (float): 时间戳（秒）
    
    Returns:
        str: SRT格式的时间戳
    """
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def generate_srt(segments, output_file):
    """
    生成SRT字幕文件
    
    Args:
        segments (list): Whisper识别结果的segments
        output_file (str): 输出SRT文件路径
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            # SRT格式：
            # 1
            # 00:00:00,000 --> 00:00:05,000
            # 字幕内容
            # 
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = segment['text'].strip()
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")
    
    print(f"SRT字幕文件已生成: {output_file}")


def transcribe_to_srt(audio_file, output_srt=None, model_name="large-v3-turbo", language="zh"):
    """
    将音频文件转录为SRT字幕文件
    
    Args:
        audio_file (str): 音频文件路径
        output_srt (str): 输出SRT文件路径，如果为None则自动生成
        model_name (str): Whisper模型名称
        language (str): 语言代码
    """
    # 检查音频文件是否存在
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"音频文件不存在: {audio_file}")
    
    # 自动生成输出文件名
    if output_srt is None:
        base_name = os.path.splitext(audio_file)[0]
        output_srt = f"{base_name}.srt"
    
    print(f"正在加载Whisper模型: {model_name}")
    model = whisper.load_model(model_name)
    
    print(f"正在转录音频文件: {audio_file}")
    result = model.transcribe(
        audio_file, 
        language=language, 
        initial_prompt="简体中文",
        word_timestamps=True  # 启用词级时间戳以获得更精确的分段
    )
    
    # 打印识别的完整文本
    print("识别结果:")
    print("-" * 50)
    print(result["text"])
    print("-" * 50)
    
    # 生成SRT文件
    if 'segments' in result and result['segments']:
        generate_srt(result['segments'], output_srt)
        
        # 显示分段信息
        print(f"\n共识别到 {len(result['segments'])} 个分段:")
        for i, segment in enumerate(result['segments'][:5], 1):  # 只显示前5个分段
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = segment['text'].strip()
            print(f"{i}. [{start_time} --> {end_time}] {text}")
        
        if len(result['segments']) > 5:
            print(f"... 还有 {len(result['segments']) - 5} 个分段")
    else:
        print("警告: 没有检测到音频分段，无法生成SRT文件")
    
    return result


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("python test.py <音频文件路径> [输出SRT文件路径] [模型名称] [语言代码]")
        print("\n示例:")
        print("python test.py qinghuanv.wav")
        print("python test.py qinghuanv.wav output.srt")
        print("python test.py qinghuanv.wav output.srt base zh")
        print("\n支持的模型: tiny, base, small, medium, large, large-v2, large-v3-turbo")
        print("常用语言代码: zh(中文), en(英文), ja(日文), ko(韩文)")
        return
    
    # 解析命令行参数
    audio_file = sys.argv[1]
    output_srt = sys.argv[2] if len(sys.argv) > 2 else None
    model_name = sys.argv[3] if len(sys.argv) > 3 else "large-v3-turbo"
    language = sys.argv[4] if len(sys.argv) > 4 else "zh"
    
    try:
        # 执行转录
        result = transcribe_to_srt(audio_file, output_srt, model_name, language)
        print("\n转录完成！")
        
    except Exception as e:
        print(f"转录失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # 如果直接运行脚本，使用命令行参数
    if len(sys.argv) > 1:
        main()
    else:
        # 保持原有的简单调用方式（向后兼容）
        print("正在使用默认设置转录 qinghuanv.wav...")
        try:
            result = transcribe_to_srt("qinghuanv.wav")
        except Exception as e:
            print(f"转录失败: {str(e)}")
            print("\n请使用以下格式指定音频文件:")
            print("python test.py <音频文件路径>")