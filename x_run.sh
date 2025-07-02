data_dir=jiqimao_`date +%Y%m%d%H%M`
data_dir=jiqimao_202507012343
voice=jiqimao
filename=$data_dir/$voice
content_file=$filename"_rewrite.txt"
title_file=$filename"_title.txt"
subtitle_file=$filename"_subtitle.txt"
tmp_file=$data_dir/tmp.mp4
content_pic=$filename.jpeg
content_video=$filename.mp4
content_video_bgm=$filename"_bgm.mp4"
content_video_rotate=$filename"_rotate.mp4"
content_video_srt=$filename"_srt.mp4"
content_video_final=$filename"_final.mp4"
content_video_bgm_rotate=$filename"_bgm_rotate.mp4"
src_srt=$filename".srt"
corrected_srt=$filename"_corrected.srt"
local_pic=picture/doutu/036.jpg
uuid=$voice
voice_file=$data_dir/$uuid.wav
bgm_file=bgm/1.wav

mkdir -p $data_dir

function content_pic_gen() {
    #内容图片生成
    python content_pic_gen.py $local_pic --padding 100 -o $content_pic
}

function content_rewrite() {
    #文案获取
    python coze_content_rewrite.py $filename
}

function cover_gen() {
    #封面生成
    if [ ! -f $title_file ] || [ ! -f $subtitle_file ]; then
        echo "标题或副标题文件不存在"
        exit 1
    fi
    python coze_cover_gen.py $data_dir $(cat $title_file) $(cat $subtitle_file)
}

function voice_gen() {
    #提交语音生成任务
    python clone_voice.py -f $content_file -o $uuid -v $voice
}

function download_wavs() {
    #下载语音
    while true; do
        if [ ! -f $voice_file ]; then
            python download_wavs.py 4 --delete-after-download -d $data_dir
        else
            echo "语音文件已存在"
            break
        fi
        sleep 10
    done
}

function rotate_image_wav() {
    #图片旋转
    cp $local_pic $content_pic
    rm -f $content_video_rotate
    sh rotate_image_wav.sh -w 1024 -h 574 -z 2 -p 50 $content_pic $voice_file $content_video_rotate
}

function video_merger() {
    #视频合成
    python video_merger.py $content_pic $voice_file $tmp_file
}

function srt_gen() {
    #语音转字幕
    rm -f $src_srt
    python srt_gen.py $filename.wav $src_srt
}

function srt_fix() {
    #字幕纠错
    if [ ! -f $src_srt ]; then
        echo "字幕文件不存在，exit"
        exit 1
    fi
    rm -f $corrected_srt
    python fix_srt.py $content_file $src_srt -o $corrected_srt
}

function srt_merge() {
    #字幕合成
    rm -f $content_video_srt
    ffmpeg -i $content_video_rotate -vf "subtitles=${corrected_srt}:force_style='FontSize=25'" $content_video_srt
}

function add_bgm() {
    # 循环背景音乐，音量20%，3秒淡入淡出
    ./add_bgm.sh -v 0.3 -l -f 1 -F 1 $content_video_srt $bgm_file $content_video_bgm
}

function add_bgm_rotate() {
    # 循环背景音乐，音量20%，3秒淡入淡出
    rm -f $content_video_bgm_rotate
    sh add_bgm.sh -v 0.3 -l -f 1 -F 1 $content_video_srt $bgm_file $content_video_bgm_rotate
}

function clear_audio_data() {
    #清空语音数据
    python api_operate.py clear 4
}

function clear_content_data() {
    #清空内容数据（包含封面图链接）
    python api_operate.py clear_content
}

function clear_dir() {
    #清空当前目录
    mv $data_dir ~/Downloads/
}

function gen_video() {
    arg=$1
    # 定义运行步骤
    run_flag="content_rewrite|cover_gen|clear_audio_data|voice_gen|download_wavs|rotate_image_wav|srt_gen|srt_fix|srt_merge|add_bgm_rotate|clear_content_data"
    #run_flag="content_pic_gen"
    #run_flag="content_rewrite"
    #run_flag="cover_gen"
    #run_flag="voice_gen"
    #run_flag="download_wavs"
    #run_flag="rotate_image_wav"
    #run_flag="srt_gen"
    #run_flag="srt_fix"
    #run_flag="srt_merge"
    #run_flag="add_bgm_rotate"
    if [ "$arg" = "re" ]; then
        run_flag="content_rewrite"
    fi
    if [ "$arg" = "co" ]; then
        run_flag="cover_gen"
    fi
    if [ "$arg" = "sf" ]; then
        run_flag="srt_fix"
    fi
    if [ "$arg" = "n" ]; then
        run_flag="cover_gen|clear_audio_data|voice_gen|download_wavs|rotate_image_wav|srt_gen|srt_fix|srt_merge|add_bgm_rotate|clear_content_data"
    fi
    if [ "$arg" = "cl" ]; then
        run_flag="clear_dir"
    fi

    # 使用数组方式分割字符串
    IFS='|' read -ra STEPS <<< "$run_flag"
    for step in "${STEPS[@]}"; do
        echo "======================================================================================="
        echo "步骤: $step"
        $step
    done
}

case $1 in
    gen)
        gen_video $2
        ;;
    clear_audio)
        clear_audio_data
        ;;
    clear_content)
        clear_content_data
        ;;
    *)
        echo "Usage: $0 {gen|clear_audio|clear_content}"
        exit 1
esac

#sh x_run.sh gen re
#sh x_run.sh gen all