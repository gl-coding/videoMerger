#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转字幕工具 - 使用faster-whisper将音频转换为SRT字幕文件
"""

from faster_whisper import WhisperModel
import os
import sys
from datetime import timedelta


def format_timestamp(seconds):
    """将秒数转换为SRT时间格式 (HH:MM:SS,mmm)"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def generate_srt(segments, output_file):
    """生成SRT字幕文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            start_time = format_timestamp(segment[0])
            end_time = format_timestamp(segment[1])
            text = segment[2].strip()

            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")

    print(f"SRT字幕文件已生成: {output_file}")

def transcribe_to_srt(audio_file, output_srt=None, model_size="large-v3", language="zh", word_output_file=None):
    """将音频文件转录为SRT字幕文件，并保存词级时间戳"""
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"音频文件不存在: {audio_file}")

    if output_srt is None:
        base_name = os.path.splitext(audio_file)[0]
        output_srt = f"{base_name}.srt"
    
    # 如果未指定词级时间戳文件路径，则根据SRT文件路径生成
    if word_output_file is None:
        word_output_file = f"{os.path.splitext(output_srt)[0]}_words.txt"

    print(f"正在加载faster-whisper模型: {model_size}")
    model = WhisperModel(model_size)

    print(f"正在转录音频文件: {audio_file}")
    segments_gen, info = model.transcribe(
        audio_file,
        language=language,
        word_timestamps=True,
        vad_filter=True
    )

    # 收集分段 + 词级时间戳
    segments = []
    word_lines = []
    full_text = ""
    for seg in segments_gen:
        start = seg.start
        end = seg.end
        text = seg.text
        segments.append((start, end, text))
        full_text += text

        if seg.words:  # 如果有词级时间戳
            for word in seg.words:
                word_line = f"{format_timestamp(word.start)} --> {format_timestamp(word.end)}  {word.word}"
                word_lines.append(word_line)

    print("识别结果:")
    print("-" * 50)
    print(full_text)
    print("-" * 50)

    if segments:
        generate_srt(segments, output_srt)

        # 写入词级时间戳文件
        with open(word_output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(word_lines))
        print(f"词级时间戳文件已生成: {word_output_file}")

        print(f"\n共识别到 {len(segments)} 个分段:")
        for i, seg in enumerate(segments[:5], 1):
            start_time = format_timestamp(seg[0])
            end_time = format_timestamp(seg[1])
            print(f"{i}. [{start_time} --> {end_time}] {seg[2].strip()}")
        if len(segments) > 5:
            print(f"... 还有 {len(segments) - 5} 个分段")
    else:
        print("警告: 没有检测到音频分段，无法生成SRT文件")

    return segments

def transcribe_to_srt_v2(audio_file, output_srt=None, model_size="large-v3", language="zh"):
    """将音频文件转录为SRT字幕文件"""
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"音频文件不存在: {audio_file}")

    if output_srt is None:
        base_name = os.path.splitext(audio_file)[0]
        output_srt = f"{base_name}.srt"

    print(f"正在加载faster-whisper模型: {model_size}")
    model = WhisperModel(model_size)

    print(f"正在转录音频文件: {audio_file}")
    segments_gen, info = model.transcribe(
        audio_file,
        language=language,
        word_timestamps=True,
        vad_filter=True
    )

    # 收集分段
    segments = []
    full_text = ""
    for seg in segments_gen:
        start = seg.start
        end = seg.end
        text = seg.text
        segments.append((start, end, text))
        full_text += text

    print("识别结果:")
    print("-" * 50)
    print(full_text)
    print("-" * 50)

    if segments:
        generate_srt(segments, output_srt)

        print(f"\n共识别到 {len(segments)} 个分段:")
        for i, seg in enumerate(segments[:5], 1):
            start_time = format_timestamp(seg[0])
            end_time = format_timestamp(seg[1])
            print(f"{i}. [{start_time} --> {end_time}] {seg[2].strip()}")
        if len(segments) > 5:
            print(f"... 还有 {len(segments) - 5} 个分段")
    else:
        print("警告: 没有检测到音频分段，无法生成SRT文件")

    return segments


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("python srt_gen.py <音频文件路径> [输出SRT文件路径] [模型大小] [语言代码] [词级时间戳文件路径]")
        print("\n示例:")
        print("python srt_gen.py qinghuanv.wav")
        print("python srt_gen.py qinghuanv.wav output.srt")
        print("python srt_gen.py qinghuanv.wav output.srt base zh")
        print("python srt_gen.py qinghuanv.wav output.srt base zh words_output.txt")
        print("\n支持的模型: tiny, base, small, medium, large, large-v2, large-v3")
        print("常用语言代码: zh(中文), en(英文), ja(日文), ko(韩文)")
        return

    audio_file = sys.argv[1]
    output_srt = sys.argv[2] if len(sys.argv) > 2 else None
    model_size = sys.argv[3] if len(sys.argv) > 3 else "large-v3"
    language = sys.argv[4] if len(sys.argv) > 4 else "zh"
    word_output_file = sys.argv[5] if len(sys.argv) > 5 else None

    try:
        transcribe_to_srt(audio_file, output_srt, model_size, language, word_output_file)
        print("\n转录完成！")
    except Exception as e:
        print(f"转录失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("正在使用默认设置转录 qinghuanv.wav...")
        try:
            transcribe_to_srt("qinghuanv.wav")
        except Exception as e:
            print(f"转录失败: {str(e)}")
            print("\n请使用以下格式指定音频文件:")
            print("python srt_gen.py <音频文件路径>")
