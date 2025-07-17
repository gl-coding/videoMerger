#!/bin/bash

# MP4视频添加WAV背景音乐脚本
# 作者: 视频合成器项目
# 用法: ./add_bgm.sh [选项] <视频文件> <音频文件> <输出文件>

# 默认参数
BGM_VOLUME="0.3"        # 背景音乐音量 (0.0-1.0)
ORIGINAL_VOLUME="1.0"   # 原视频音量 (0.0-1.0)
MIX_MODE="mix"          # 混合模式: mix(混合) 或 replace(替换)
LOOP_BGM="false"        # 是否循环背景音乐
FADE_IN="0"             # 背景音乐淡入时间(秒)
FADE_OUT="0"            # 背景音乐淡出时间(秒)

# 显示帮助信息
show_help() {
    echo "MP4视频添加WAV背景音乐工具"
    echo ""
    echo "用法:"
    echo "  $0 [选项] <视频文件> <音频文件> <输出文件>"
    echo ""
    echo "选项:"
    echo "  -v, --bgm-volume VOLUME     背景音乐音量 (0.0-1.0, 默认: 0.3)"
    echo "  -o, --original-volume VOL   原视频音量 (0.0-1.0, 默认: 1.0)"
    echo "  -m, --mode MODE             混合模式: mix(混合) 或 replace(替换), 默认: mix"
    echo "  -l, --loop                  循环背景音乐直到视频结束"
    echo "  -f, --fade-in SECONDS       背景音乐淡入时间(秒)"
    echo "  -F, --fade-out SECONDS      背景音乐淡出时间(秒)"
    echo "  -h, --help                  显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  # 基本用法 - 混合音频，背景音乐音量30%"
    echo "  $0 video.mp4 bgm.wav output.mp4"
    echo ""
    echo "  # 替换原音频"
    echo "  $0 -m replace video.mp4 bgm.wav output.mp4"
    echo ""
    echo "  # 循环背景音乐，音量20%，3秒淡入淡出"
    echo "  $0 -v 0.2 -l -f 3 -F 3 video.mp4 bgm.wav output.mp4"
    echo ""
    echo "  # 降低原音频音量到50%，背景音乐40%"
    echo "  $0 -v 0.4 -o 0.5 video.mp4 bgm.wav output.mp4"
}

# 检查依赖
check_dependencies() {
    if ! command -v ffmpeg &> /dev/null; then
        echo "错误: 未找到 ffmpeg，请先安装 ffmpeg"
        echo "macOS: brew install ffmpeg"
        echo "Ubuntu: sudo apt install ffmpeg"
        exit 1
    fi
}

# 检查文件是否存在
check_files() {
    local video_file="$1"
    local audio_file="$2"
    
    if [[ ! -f "$video_file" ]]; then
        echo "错误: 视频文件不存在: $video_file"
        exit 1
    fi
    
    if [[ ! -f "$audio_file" ]]; then
        echo "错误: 音频文件不存在: $audio_file"
        exit 1
    fi
}

# 获取视频时长(秒)
get_video_duration() {
    local video_file="$1"
    ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$video_file"
}

# 构建音频滤镜
build_audio_filter() {
    local mode="$1"
    local bgm_vol="$2"
    local orig_vol="$3"
    local fade_in="$4"
    local fade_out="$5"
    local video_duration="$6"
    
    local filter=""
    
    if [[ "$mode" == "replace" ]]; then
        # 替换模式 - 只使用背景音乐
        filter="[1:a]volume=${bgm_vol}"
        
        # 添加淡入淡出效果
        if [[ "$fade_in" != "0" ]]; then
            filter="${filter},afade=t=in:st=0:d=${fade_in}"
        fi
        
        if [[ "$fade_out" != "0" ]]; then
            filter="${filter},afade=t=out:st=$((${video_duration%.*} - fade_out)):d=${fade_out}"
        fi
        
        filter="${filter}[aout]"
    else
        # 混合模式 - 混合原音频和背景音乐
        filter="[0:a]volume=${orig_vol}[orig];"
        filter="${filter}[1:a]volume=${bgm_vol}"
        
        # 添加淡入淡出效果
        if [[ "$fade_in" != "0" ]]; then
            filter="${filter},afade=t=in:st=0:d=${fade_in}"
        fi
        
        if [[ "$fade_out" != "0" ]]; then
            filter="${filter},afade=t=out:st=$((${video_duration%.*} - fade_out)):d=${fade_out}"
        fi
        
        filter="${filter}[bg];[orig][bg]amix=inputs=2:duration=first:dropout_transition=3[aout]"
    fi
    
    echo "$filter"
}

# 主处理函数
process_video() {
    local video_file="$1"
    local audio_file="$2"
    local output_file="$3"
    
    echo "开始处理视频..."
    echo "视频文件: $video_file"
    echo "音频文件: $audio_file"
    echo "输出文件: $output_file"
    echo "混合模式: $MIX_MODE"
    echo "背景音乐音量: $BGM_VOLUME"
    echo "原视频音量: $ORIGINAL_VOLUME"
    echo "循环背景音乐: $LOOP_BGM"
    
    # 获取视频时长
    local video_duration=$(get_video_duration "$video_file")
    echo "视频时长: ${video_duration}秒"
    
    # 构建ffmpeg命令
    local ffmpeg_cmd="ffmpeg -y -i \"$video_file\""
    
    # 添加音频输入
    if [[ "$LOOP_BGM" == "true" ]]; then
        ffmpeg_cmd="$ffmpeg_cmd -stream_loop -1 -i \"$audio_file\""
    else
        ffmpeg_cmd="$ffmpeg_cmd -i \"$audio_file\""
    fi
    
    # 构建音频滤镜
    local audio_filter=$(build_audio_filter "$MIX_MODE" "$BGM_VOLUME" "$ORIGINAL_VOLUME" "$FADE_IN" "$FADE_OUT" "$video_duration")
    
    # 添加滤镜和输出选项
    ffmpeg_cmd="$ffmpeg_cmd -filter_complex \"$audio_filter\" -map 0:v:0 -map \"[aout]\" -c:v copy -c:a aac -shortest \"$output_file\""
    
    echo ""
    echo "执行命令:"
    echo "$ffmpeg_cmd"
    echo ""
    
    # 执行命令
    eval $ffmpeg_cmd
    
    if [[ $? -eq 0 ]]; then
        echo ""
        echo "✅ 处理完成！输出文件: $output_file"
        
        # 显示文件信息
        if command -v ffprobe &> /dev/null; then
            echo ""
            echo "输出文件信息:"
            ffprobe -v quiet -show_entries format=duration,format=size -of csv=p=0 "$output_file" | while IFS=, read duration size; do
                echo "  时长: ${duration}秒"
                echo "  大小: $((size / 1024 / 1024))MB"
            done
        fi
    else
        echo ""
        echo "❌ 处理失败！"
        exit 1
    fi
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--bgm-volume)
                BGM_VOLUME="$2"
                shift 2
                ;;
            -o|--original-volume)
                ORIGINAL_VOLUME="$2"
                shift 2
                ;;
            -m|--mode)
                MIX_MODE="$2"
                shift 2
                ;;
            -l|--loop)
                LOOP_BGM="true"
                shift
                ;;
            -f|--fade-in)
                FADE_IN="$2"
                shift 2
                ;;
            -F|--fade-out)
                FADE_OUT="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                echo "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                # 位置参数
                if [[ -z "$VIDEO_FILE" ]]; then
                    VIDEO_FILE="$1"
                elif [[ -z "$AUDIO_FILE" ]]; then
                    AUDIO_FILE="$1"
                elif [[ -z "$OUTPUT_FILE" ]]; then
                    OUTPUT_FILE="$1"
                else
                    echo "错误: 参数过多"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# 主函数
main() {
    # 解析参数
    parse_args "$@"
    
    # 检查必需参数
    if [[ -z "$VIDEO_FILE" ]] || [[ -z "$AUDIO_FILE" ]] || [[ -z "$OUTPUT_FILE" ]]; then
        echo "错误: 缺少必需参数"
        echo ""
        show_help
        exit 1
    fi
    
    # ���证参数
    if [[ "$MIX_MODE" != "mix" ]] && [[ "$MIX_MODE" != "replace" ]]; then
        echo "错误: 混合模式只能是 'mix' 或 'replace'"
        exit 1
    fi
    
    # 检查依赖和文件
    check_dependencies
    check_files "$VIDEO_FILE" "$AUDIO_FILE"
    
    # 处理视频
    process_video "$VIDEO_FILE" "$AUDIO_FILE" "$OUTPUT_FILE"
}

# 运行主函数
main "$@"