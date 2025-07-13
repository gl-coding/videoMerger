import re, sys
from datetime import datetime, timedelta

def parse_timestamp(ts_str):
    """解析SRT时间戳"""
    return datetime.strptime(ts_str, "%H:%M:%S,%f")

def format_timestamp(dt):
    """格式化为SRT时间戳"""
    return dt.strftime("%H:%M:%S,%f")[:-3]

def generate_srt_from_words(words_file, output_srt):
    with open(words_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    subs = []
    current_start = None
    current_end = None
    current_text = ""
    index = 1

    # 正则匹配时间戳行
    pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+(.*)")

    for line in lines:
        match = pattern.match(line)
        if match:
            start_ts = parse_timestamp(match.group(1))
            end_ts = parse_timestamp(match.group(2))
            word = match.group(3)

            if current_start is None:
                current_start = start_ts

            current_end = end_ts
            current_text += word

            # 检查单词是否以标点符号结尾
            if word and word[-1] in "，。！？,.!?":
                subs.append((
                    format_timestamp(current_start),
                    format_timestamp(current_end),
                    current_text.strip()
                ))
                current_start = None
                current_end = None
                current_text = ""

    # 最后一句如果没标点，也写入
    if current_text:
        subs.append((
            format_timestamp(current_start),
            format_timestamp(current_end),
            current_text.strip()
        ))

    # 写 SRT 文件
    with open(output_srt, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(subs, 1):
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")

    print(f"SRT字幕文件已生成: {output_srt}")

# 调用方法
if __name__ == "__main__":  
    words_txt = sys.argv[1]
    output_srt = sys.argv[2]
    generate_srt_from_words(words_txt, output_srt)

