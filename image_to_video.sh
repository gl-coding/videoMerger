#!/bin/bash

# 将图片和音频合成为视频，支持多种动态效果
# 用法: ./image_to_video.sh [选项] <图片文件> <音频文件> <输出视频>

# 默认参数
WIDTH="1920"           # 输出宽度
HEIGHT="1080"          # 输出高度
FPS="30"               # 帧率
ZOOM="1.0"             # 缩放比例
BG_COLOR="black"       # 背景颜色
AUDIO_VOLUME="1.0"     # 音频音量
EFFECT="none"          # 动态效果
EFFECT_SPEED="1.0"     # 效果速度

# 显示帮助信息
show_help() {
    echo "将图片和音频合成为视频，支持多种动态效果"
    echo ""
    echo "用法:"
    echo "  $0 [选项] <图片文件> <音频文件> <输出视频文件>"
    echo ""
    echo "选项:"
    echo "  -w, --width WIDTH           输出宽度(默认: 1920)"
    echo "  -h, --height HEIGHT         输出高度(默认: 1080)"
    echo "  -f, --fps FPS               帧率(默认: 30)"
    echo "  -z, --zoom SCALE            缩放比例(默认: 1.0)"
    echo "  -b, --background COLOR      背景颜色(默认: black)"
    echo "  -v, --volume LEVEL          音频音量(默认: 1.0)"
    echo "  -e, --effect EFFECT         动态效果(默认: none)"
    echo "                              可选: none, kenburns, move_right, move_left,"
    echo "                                    move_up, move_down, fade, swing"
    echo "  -s, --speed SPEED           效果速度(默认: 1.0)"
    echo "  --help                      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  # 基本用法"
    echo "  $0 image.jpg audio.wav output.mp4"
    echo ""
    echo "  # 添加Ken Burns效果"
    echo "  $0 -e kenburns image.jpg audio.wav output.mp4"
    echo ""
    echo "  # 添加移动效果"
    echo "  $0 -e move_right -s 0.5 image.jpg audio.wav output.mp4"
}

# 检查依赖
check_dependencies() {
    if ! command -v ffmpeg &> /dev/null; then
        echo "错误: 未找到 ffmpeg，请先安装 ffmpeg"
        exit 1
    fi
    
    if ! command -v ffprobe &> /dev/null; then
        echo "错误: 未找到 ffprobe，请先安装 ffmpeg"
        exit 1
    fi
}

# 检查文件
check_files() {
    local image_file="$1"
    local audio_file="$2"
    
    if [[ ! -f "$image_file" ]]; then
        echo "错误: 图片文件不存在: $image_file"
        exit 1
    fi
    
    if [[ ! -f "$audio_file" ]]; then
        echo "错误: 音频文件不存在: $audio_file"
        exit 1
    fi
}

# 获取音频时长
get_audio_duration() {
    local audio_file="$1"
    
    echo "正在检测音频时长..." >&2
    local duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$audio_file" 2>/dev/null)
    
    if [[ -z "$duration" ]] || [[ "$duration" == "N/A" ]]; then
        echo "错误: 无法获取音频文件时长" >&2
        exit 1
    fi
    
    # 取整数部分（向上取整）
    duration=$(echo "$duration" | awk '{printf "%.0f", $1 + 0.5}')
    
    echo "音频时长: ${duration}秒" >&2
    echo "$duration"
}

# 生成视频
generate_video() {
    local image_file="$1"
    local audio_file="$2"
    local output_file="$3"
    local duration="$4"
    
    echo ""
    echo "开始生成视频..."
    echo "图片文件: $image_file"
    echo "音频文件: $audio_file"
    echo "输出文件: $output_file"
    echo "视频时长: ${duration}秒"
    echo "输出尺寸: ${WIDTH}x${HEIGHT}"
    echo "帧率: ${FPS}fps"
    echo "缩放: ${ZOOM}"
    echo "背景: $BG_COLOR"
    echo "音频音量: ${AUDIO_VOLUME}"
    echo "动态效果: $EFFECT"
    echo "效果速度: ${EFFECT_SPEED}"
    
    # 确保宽度和高度都是偶数（H.264编码器要求）
    WIDTH=$(( (WIDTH + 1) / 2 * 2 ))
    HEIGHT=$(( (HEIGHT + 1) / 2 * 2 ))
    
    # 构建FFmpeg命令
    local ffmpeg_cmd="ffmpeg -y"
    ffmpeg_cmd="$ffmpeg_cmd -loop 1 -i \"$image_file\""
    ffmpeg_cmd="$ffmpeg_cmd -i \"$audio_file\""
    ffmpeg_cmd="$ffmpeg_cmd -f lavfi -i color=c=${BG_COLOR}:s=${WIDTH}x${HEIGHT}:r=${FPS}"
    ffmpeg_cmd="$ffmpeg_cmd -filter_complex \""
    
    # 根据选择的效果应用不同的滤镜
    case $EFFECT in
        "kenburns")
            # Ken Burns效果：缓慢放大
            local zoom_speed=$(echo "0.0005 * $EFFECT_SPEED" | bc)
            ffmpeg_cmd="$ffmpeg_cmd[0:v]format=yuv420p,scale=iw*${ZOOM}:ih*${ZOOM},zoompan=z='min(zoom+${zoom_speed},1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${duration}:s=${WIDTH}x${HEIGHT}[scaled];"
            ;;
        "move_right")
            # 向右移动
            local move_speed=$(echo "20 * $EFFECT_SPEED" | bc)
            ffmpeg_cmd="$ffmpeg_cmd[0:v]format=yuv420p,scale=iw*${ZOOM}:ih*${ZOOM},crop=${WIDTH}:${HEIGHT}:x='t*${move_speed}':y=0[scaled];"
            ;;
        "move_left")
            # 向左移动
            local move_speed=$(echo "20 * $EFFECT_SPEED" | bc)
            ffmpeg_cmd="$ffmpeg_cmd[0:v]format=yuv420p,scale=iw*${ZOOM}:ih*${ZOOM},crop=${WIDTH}:${HEIGHT}:x='max(iw-w-t*${move_speed},0)':y=0[scaled];"
            ;;
        "move_up")
            # 向上移动
            local move_speed=$(echo "20 * $EFFECT_SPEED" | bc)
            ffmpeg_cmd="$ffmpeg_cmd[0:v]format=yuv420p,scale=iw*${ZOOM}:ih*${ZOOM},crop=${WIDTH}:${HEIGHT}:x=0:y='max(ih-h-t*${move_speed},0)'[scaled];"
            ;;
        "move_down")
            # 向下移动
            local move_speed=$(echo "20 * $EFFECT_SPEED" | bc)
            ffmpeg_cmd="$ffmpeg_cmd[0:v]format=yuv420p,scale=iw*${ZOOM}:ih*${ZOOM},crop=${WIDTH}:${HEIGHT}:x=0:y='t*${move_speed}'[scaled];"
            ;;
        "fade")
            # 淡入淡出效果
            local fade_out_start=$(echo "${duration}-2" | bc)
            ffmpeg_cmd="$ffmpeg_cmd[0:v]format=yuv420p,scale=iw*${ZOOM}:ih*${ZOOM},fade=t=in:st=0:d=2,fade=t=out:st=${fade_out_start}:d=2[scaled];"
            ;;
        "swing")
            # 轻微摇摆效果
            local swing_speed=$(echo "8 / $EFFECT_SPEED" | bc)
            ffmpeg_cmd="$ffmpeg_cmd[0:v]format=yuv420p,scale=iw*${ZOOM}:ih*${ZOOM},rotate='sin(t*PI/${swing_speed})*2':c=${BG_COLOR}[scaled];"
            ;;
        *)
            # 无效果
            ffmpeg_cmd="$ffmpeg_cmd[0:v]format=yuv420p,scale=iw*${ZOOM}:ih*${ZOOM}[scaled];"
            ;;
    esac
    
    ffmpeg_cmd="$ffmpeg_cmd[scaled]scale='min(${WIDTH},iw)':'min(${HEIGHT},ih)':force_original_aspect_ratio=decrease[resized];"
    ffmpeg_cmd="$ffmpeg_cmd[2:v][resized]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2[video];"
    ffmpeg_cmd="$ffmpeg_cmd[1:a]volume=${AUDIO_VOLUME}[audio]"
    ffmpeg_cmd="$ffmpeg_cmd\" -map \"[video]\" -map \"[audio]\""
    ffmpeg_cmd="$ffmpeg_cmd -t ${duration} -r ${FPS} -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k -pix_fmt yuv420p \"$output_file\""
    
    echo ""
    echo "执行命令:"
    echo "$ffmpeg_cmd"
    echo ""
    
    # 执行命令
    eval $ffmpeg_cmd
    
    if [[ $? -eq 0 ]]; then
        echo ""
        echo "✅ 视频生成完成！"
        echo "输出文件: $output_file"
        
        # 显示文件信息
        echo ""
        echo "输出文件信息:"
        ffprobe -v quiet -show_entries format=duration,format=size -of csv=p=0 "$output_file" | while IFS=, read duration size; do
            echo "  时长: ${duration}秒"
            echo "  大小: $((size / 1024 / 1024))MB"
        done
    else
        echo ""
        echo "❌ 生成失败！"
        exit 1
    fi
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -w|--width)
                WIDTH="$2"
                shift 2
                ;;
            -h|--height)
                HEIGHT="$2"
                shift 2
                ;;
            -f|--fps)
                FPS="$2"
                shift 2
                ;;
            -z|--zoom)
                ZOOM="$2"
                shift 2
                ;;
            -b|--background)
                BG_COLOR="$2"
                shift 2
                ;;
            -v|--volume)
                AUDIO_VOLUME="$2"
                shift 2
                ;;
            -e|--effect)
                EFFECT="$2"
                shift 2
                ;;
            -s|--speed)
                EFFECT_SPEED="$2"
                shift 2
                ;;
            --help)
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
                if [[ -z "$IMAGE_FILE" ]]; then
                    IMAGE_FILE="$1"
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
    if [[ -z "$IMAGE_FILE" ]] || [[ -z "$AUDIO_FILE" ]] || [[ -z "$OUTPUT_FILE" ]]; then
        echo "错误: 缺少必需参数"
        echo ""
        show_help
        exit 1
    fi
    
    # 检查依赖和文件
    check_dependencies
    check_files "$IMAGE_FILE" "$AUDIO_FILE"
    
    # 获取音频时长
    local duration=$(get_audio_duration "$AUDIO_FILE")
    
    # 生成视频
    generate_video "$IMAGE_FILE" "$AUDIO_FILE" "$OUTPUT_FILE" "$duration"
}

# 运行主函数
main "$@" 