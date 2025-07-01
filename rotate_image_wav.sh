#!/bin/bash

# 根据音频文件时长生成旋转视频
# 用法: ./rotate_with_audio.sh [选项] <图片文件> <音频文件> <输出视频>

# 默认参数
ROTATION_SPEED="36"     # 旋转速度(度/秒，360度=完整一圈)
WIDTH="1920"           # 输出宽度
HEIGHT="1080"          # 输出高度
FPS="30"               # 帧率
DIRECTION="clockwise"   # 旋转方向: clockwise(顺时针) 或 counterclockwise(逆时针)
ZOOM="1.0"             # 缩放比例
BG_COLOR="black"       # 背景颜色
PADDING="0"            # 图片周围的内边距(像素)
AUDIO_VOLUME="1.0"     # 音频音量

# 显示帮助信息
show_help() {
    echo "根据音频文件时长生成旋转视频"
    echo ""
    echo "用法:"
    echo "  $0 [选项] <图片文件> <音频文件> <输出视频文件>"
    echo ""
    echo "选项:"
    echo "  -s, --speed DEGREES         旋转速度(度/秒, 默认: 36, 即10秒一圈)"
    echo "  -w, --width WIDTH           输出宽度(默认: 1920)"
    echo "  -h, --height HEIGHT         输出高度(默认: 1080)"
    echo "  -f, --fps FPS               帧率(默认: 30)"
    echo "  -r, --direction DIR         旋转方向: clockwise 或 counterclockwise (默认: clockwise)"
    echo "  -z, --zoom SCALE            缩放比例(默认: 1.0)"
    echo "  -b, --background COLOR      背景颜色(默认: black)"
    echo "  -p, --padding PIXELS        图片周围内边距(像素, 默认: 0)"
    echo "  -v, --volume LEVEL          音频音量(默认: 1.0)"
    echo "  --help                      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  # 基本用法 - 根据音频时长旋转"
    echo "  $0 image.jpg audio.wav output.mp4"
    echo ""
    echo "  # 自定义旋转速度和背景"
    echo "  $0 -s 72 -b white image.jpg audio.wav output.mp4"
    echo ""
    echo "  # 添加内边距和调整音量"
    echo "  $0 -p 50 -v 0.8 image.jpg audio.wav output.mp4"
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

# 生成旋转视频
generate_rotating_video() {
    local image_file="$1"
    local audio_file="$2"
    local output_file="$3"
    local duration="$4"
    
    echo ""
    echo "开始生成旋转视频..."
    echo "图片文件: $image_file"
    echo "音频文件: $audio_file"
    echo "输出文件: $output_file"
    echo "视频时长: ${duration}秒"
    echo "旋转速度: ${ROTATION_SPEED}度/秒"
    echo "旋转方向: $DIRECTION"
    echo "输出尺寸: ${WIDTH}x${HEIGHT}"
    echo "帧率: ${FPS}fps"
    echo "缩放: ${ZOOM}"
    echo "背景: $BG_COLOR"
    echo "内边距: ${PADDING}px"
    echo "音频音量: ${AUDIO_VOLUME}"
    
    # 确保宽度和高度都是偶数（H.264编码器要求）
    WIDTH=$(( (WIDTH + 1) / 2 * 2 ))
    HEIGHT=$(( (HEIGHT + 1) / 2 * 2 ))
    
    # 计算旋转方向
    local rotation_expr=""
    if [[ "$DIRECTION" == "counterclockwise" ]]; then
        rotation_expr="PI*2*t*${ROTATION_SPEED}/360"
    else
        rotation_expr="-PI*2*t*${ROTATION_SPEED}/360"
    fi
    
    # 计算实际可用尺寸（减去内边距）
    local usable_width=$((WIDTH - 2 * PADDING))
    local usable_height=$((HEIGHT - 2 * PADDING))
    
    # 构建FFmpeg命令
    local ffmpeg_cmd="ffmpeg -y"
    ffmpeg_cmd="$ffmpeg_cmd -loop 1 -i \"$image_file\""
    ffmpeg_cmd="$ffmpeg_cmd -i \"$audio_file\""
    ffmpeg_cmd="$ffmpeg_cmd -f lavfi -i color=c=${BG_COLOR}:s=${WIDTH}x${HEIGHT}:r=${FPS}"
    ffmpeg_cmd="$ffmpeg_cmd -filter_complex \""
    ffmpeg_cmd="$ffmpeg_cmd[0:v]scale=iw*${ZOOM}:ih*${ZOOM}[scaled];"
    
    if [[ "$PADDING" -gt 0 ]]; then
        # 有内边距时，先旋转再限制尺寸
        ffmpeg_cmd="$ffmpeg_cmd[scaled]rotate=${rotation_expr}:fillcolor=${BG_COLOR}[rotated_full];"
        ffmpeg_cmd="$ffmpeg_cmd[rotated_full]scale='min(${usable_width},iw)':'min(${usable_height},ih)':force_original_aspect_ratio=decrease[rotated];"
    else
        # 无内边距时，直接指定输出尺寸
        ffmpeg_cmd="$ffmpeg_cmd[scaled]rotate=${rotation_expr}:fillcolor=${BG_COLOR}:ow=${WIDTH}:oh=${HEIGHT}[rotated];"
    fi
    
    ffmpeg_cmd="$ffmpeg_cmd[2:v][rotated]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2[video];"
    ffmpeg_cmd="$ffmpeg_cmd[1:a]volume=${AUDIO_VOLUME}[audio]"
    ffmpeg_cmd="$ffmpeg_cmd\" -map \"[video]\" -map \"[audio]\""
    ffmpeg_cmd="$ffmpeg_cmd -t ${duration} -r ${FPS} -c:v libx264 -c:a aac -pix_fmt yuv420p \"$output_file\""
    
    echo ""
    echo "执行命令:"
    echo "$ffmpeg_cmd"
    echo ""
    
    # 执行命令
    eval $ffmpeg_cmd
    
    if [[ $? -eq 0 ]]; then
        echo ""
        echo "✅ 旋转视频生成完成！"
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
            -s|--speed)
                ROTATION_SPEED="$2"
                shift 2
                ;;
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
            -r|--direction)
                DIRECTION="$2"
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
            -p|--padding)
                PADDING="$2"
                shift 2
                ;;
            -v|--volume)
                AUDIO_VOLUME="$2"
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
    
    # 验证方向参数
    if [[ "$DIRECTION" != "clockwise" ]] && [[ "$DIRECTION" != "counterclockwise" ]]; then
        echo "错误: 旋转方向只能是 'clockwise' 或 'counterclockwise'"
        exit 1
    fi
    
    # 检查依赖和文件
    check_dependencies
    check_files "$IMAGE_FILE" "$AUDIO_FILE"
    
    # 获取音频时长
    local duration=$(get_audio_duration "$AUDIO_FILE")
    
    # 生成旋转视频
    generate_rotating_video "$IMAGE_FILE" "$AUDIO_FILE" "$OUTPUT_FILE" "$duration"
}

# 运行主函数
main "$@"