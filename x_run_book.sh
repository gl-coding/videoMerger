data_dir=jiqimao
voice=dushunan
name=kumi的读书日记
filename=$data_dir/result
#content
content_file=$filename"_text_rewrite.txt"
content_file_fix=$filename"_text_rewrite_fix.txt"
title_file=$filename"_text_title.txt"
subtitle_file=$filename"_text_subtitle.txt"
tmp_file=$data_dir/tmp.mp4
#video
content_video_bgm=$filename"_video_bgm.mp4"
content_video_pic=$filename"_video_pic.mp4"
content_video_srt=$filename"_video_srt.mp4"
content_video_bg_srt=$filename"_video_bg_srt.mp4"
content_video_bg_srt_ass=$filename"_video_bg_srt_ass.mp4"
content_video_bg_srt_ass_header=$filename"_video_bg_srt_ass_header.mp4"
content_video_bg_srt_ass_header_bgm=$filename"_video_bg_srt_ass_header_bgm.mp4"
#srt
src_srt=$filename"_srt.srt"
corrected_srt=$filename"_srt_corrected.srt"
srt_ass=$filename"_srt.ass"
sentence_mapping_file=$filename"_srt_stc_mapping.txt"
#pic
local_pic=picture/doutu/013.jpg
#content_pic=$filename"_pic.jpeg"
#cover
content_pic=$data_dir/pic_cover_0.jpg

#wav
uuid=result
voice_file=$data_dir/$uuid.wav
bgm_file=bgm/8.wav

function cover_video_gen() {
    #使用ffmpeg在一张图片上生成多个文字，每个文字使用不同的字体、颜色、大小、位置
    rm -f $cover_pic_text
    ffmpeg -i $cover_pic -vf "drawtext=text='《$(cat $title_file)》':fontfile=./font/Aa剑豪体.ttf:fontsize=160:fontcolor=black@0.8:x=(W-tw)/2:y=100:" $cover_pic_text
    rm -f $cover_pic_text_first
    ffmpeg -i $cover_pic_first -vf "drawtext=text='《$(cat $title_file)》':fontfile=./font/Aa剑豪体.ttf:fontsize=160:fontcolor=black@0.8:x=(W-tw)/2:y=100:" $cover_pic_text_first
    #使用ffmpeg生成一秒的视频，视频内容为cover_pic_text_first，视频时长为1秒，图片效果为fade
    rm -f $cover_pic_video
    #在视频滤镜中添加了淡出效果：fade=t=out:st=2:d=1
    #t=out：指定淡出效果
    #st=2：淡出效果从第2秒开始
    #d=1：淡出效果持续1秒
    ffmpeg -loop 1 -i $cover_pic_text_first -t 2 -c:v libx264 -pix_fmt yuv420p -vf "scale=1920:1080,fade=t=out:st=1:d=1" $cover_pic_video
}

# 获取内容图片
function content_pic_get() {
    python3 coze_content_pic_gen.py $data_dir "$(cat $title_file)"
}

#content_pic_get

# 提交获取语音任务
function voice_gen() {
    python remove_ending_numbers.py $content_file $content_file_fix
    #提交语音生成任务
    python clone_voice.py -f $content_file_fix -o $uuid -v $voice
}

# 提交获取语音任务
function cover_voice_gen() {
    clear_audio_data
    text=$1
    name=$2
    mkdir -p $name
    wavfile=$name/result.wav
    rm -f $wavfile
    echo $text > $name/$name.txt
    #提交语音生成任务
    python clone_voice.py -f $name/$name.txt -o $uuid -v $voice
    #下载语音
    rm -f $wavfile
    while true; do
        if [ ! -f $wavfile ]; then
            python download_wavs.py 4 --delete-after-download -d $name
        else
            echo "语音文件已存在"
            break
        fi
        sleep 10
    done
    #合并语音
    #ffmpeg -i $voice_file -i $cover_pic_video -c:v libx264 -c:a aac -strict experimental -shortest $content_video_bgm
    #合并字幕
    #ffmpeg -i $content_video_bgm -vf "ass=$srt_ass:fontsdir=./font" -c:a copy $content_video_bgm_ass
}

function download_wavs() {
    #下载语音
    rm -f $voice_file
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

function cover_srt_gen() {
    dir=$1
    text=$2
    echo "cover_srt_gen $dir $text"
    cover_pic_dir=$dir
    cover_pic=$cover_pic_dir/cover_pic.jpg
    cover_pic_text=$cover_pic_dir/cover_pic_text.jpg
    cover_pic_first=$cover_pic_dir/cover_pic_first.jpg
    cover_pic_text_first=$cover_pic_dir/cover_pic_text_first.jpg
    cover_pic_video=$cover_pic_dir/cover_pic_video.mp4
    cover_video_ass=$cover_pic_dir/cover_video_ass.mp4
    cover_voice_file=$cover_pic_dir/result.wav
    cover_voice_srt=$cover_pic_dir/cover_voice_srt.srt
    cover_voice_srt_ass=$cover_pic_dir/cover_voice_srt_ass.ass
    cover_video_wav=$cover_pic_dir/cover_video_wav.mp3

    mkdir -p $cover_pic_dir
    cp cover/cover_pic_text_first.jpg $cover_pic_text_first

    #生成语音
    cover_voice_gen $text $cover_pic_dir
    #生成字幕
    rm -f $cover_voice_srt
    python srt_gen.py $cover_voice_file $cover_voice_srt 
    #生成图片视频
    rm -f $cover_pic_video
    sh image_to_video.sh $cover_pic_text_first $cover_voice_file $cover_pic_video -e zoom_in -s 2.0 --final-zoom 2.0
    #生成ass文件
    rm -f $cover_voice_srt_ass
    python3 srt2ass_with_effect.py $cover_voice_srt $cover_voice_srt_ass --align 2 --font "鸿雷板书简体-正式版" --size 120 --color white  
    #mp4合并ass
    rm -f $cover_video_ass
    ffmpeg -i $cover_pic_video -vf "ass=$cover_voice_srt_ass:fontsdir=./font" -c:a copy $cover_video_ass
}

function cover_video_gen_all() {
    # 生成封面视频
    cover_srt_gen "aaa" "今天我们分享的是"
    cover_srt_gen "bbb" "余华老师的《活着》"

    # 合并封面视频
    echo "file 'aaa/cover_video_ass.mp4'" > cover_list.txt
    echo "file 'bbb/cover_video_ass.mp4'" >> cover_list.txt
    
    # 合并视频
    rm -f merged_cover.mp4
    ffmpeg -f concat -safe 0 -i cover_list.txt -c copy merged_cover.mp4
    
    echo "封面视频合并完成: cover/merged_cover.mp4"
    
    # 删除临时文件
    rm cover_list.txt
}

#voice_gen
#download_wavs
#exit

function content_video_pic_gen() {
    rm -f $content_video_pic
    #sh image_to_video.sh $content_pic $voice_file $content_video_pic -e fade
    #sh image_to_video.sh $content_pic $voice_file $content_video_pic -e kenburns
    sh image_to_video.sh $content_pic $voice_file $content_video_pic -e zoom_in -s 2.0 --final-zoom 2.0
    #sh image_to_video.sh $content_pic $voice_file $content_video_pic -e move_down   
}

#content_video_pic_gen

function srt_gen() {
    #语音转字幕
    rm -f $src_srt
    python srt_gen.py $voice_file $src_srt 
}

#srt_gen

function srt_fix() {
    #字幕纠错
    if [ ! -f $src_srt ]; then
        echo "字幕文件不存在，exit"
        exit 1
    fi
    rm -f $corrected_srt
    rm -f $sentence_mapping_file
    python fix_srt.py $src_srt $content_file_fix -o $corrected_srt 
}

function srt_ass_gen() {
    ## 特效
    # fade（默认）- 淡入淡出效果
    # move_right - 从左向右移动
    # move_left - 从右向左移动
    # move_up - 从下向上移动
    # move_down - 从上向下移动
    # zoom - 放大效果
    # rotate - 360度旋转
    # shake - 抖动效果
    # wave - 波浪效果
    # none - 无特效 
    #生成ass文件
    #rm -f jiqimao/result_srt.ass
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 120 --color white --effect zoom --color2 red --split 3 --size2 160 --highlight
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 120 --color white --effect zoom  --highlight --keyword-size 160 
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 120 --color white --effect zoom  --highlight --keyword-size 160 --per-line --dict-file jiqimao/dict.txt --skip-lines "1,2"
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 120 --color white  --highlight --keyword-size 160 --per-line --dict-file jiqimao/dict.txt --skip-lines "1,2" --effects "fade,move_right,move_left"
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 120 --color white  --highlight --keyword-size 160 --per-line --dict-file jiqimao/dict.txt --skip-lines "1,2" --effect zoom
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect rotate
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect shake
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect wave
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect bounce
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect move_up
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect move_down
    #python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect move_right
    python3 srt2ass_with_effect.py $corrected_srt $srt_ass --align 5 --font "鸿雷板书简体-正式版" --size 120 --color white  --effect zoom
}

#srt_ass_gen
#exit 0

# 添加背景文字
function video_bg_srt_gen() {
    rm -f $content_video_bg_srt
    ffmpeg -i $content_video_pic -vf "drawtext=text='《$(cat $title_file)》':fontfile=./font/Aa剑豪体.ttf:fontsize=160:fontcolor=red@0.8:x=(W-tw)/2:y=100:" $content_video_bg_srt
}

#video_bg_srt_gen
#exit 0

# 用新字体生成mp4字幕文件
function video_bg_srt_ass_gen() {
    rm -f $content_video_bg_srt_ass
    #ffmpeg -i jiqimao/result_video_rotate.mp4 -vf "ass=jiqimao/result_srt.ass" -c:a copy output.mp4
    ffmpeg -i $content_video_bg_srt -vf "ass=$srt_ass:fontsdir=./font" -c:a copy $content_video_bg_srt_ass
}

#video_bg_srt_ass_gen
#exit 0

# 添加水印
function video_bg_srt_ass_header_gen() {
    rm -f $content_video_bg_srt_ass_header
    ffmpeg -i $content_video_bg_srt_ass -vf "drawtext=text='@$name':fontfile=./font/鸿雷板书简体-正式版.ttf:fontsize=36:fontcolor=white:x=10:y=10" $content_video_bg_srt_ass_header

    #rm -f out2.mp4
    #ffmpeg -i out1.mp4 -vf "drawtext=text='@版权所有':fontfile=./font/鸿雷板书简体-正式版.ttf:fontsize=36:fontcolor=white@0.8:x=W-tw-10:y=10:shadowcolor=black:shadowx=2:shadowy=2" out2.mp4
}

#video_bg_srt_ass_header_gen

function video_add_bgm() {
    # 循环背景音乐，音量20%，3秒淡入淡出
    rm -f $content_video_bg_srt_ass_header_bgm
    sh add_bgm.sh -v 0.4 -l -f 1 -F 1 $content_video_bg_srt_ass_header $bgm_file $content_video_bg_srt_ass_header_bgm
}

#add_bgm_rotate
#exit 0
#video_add_bgm

function clear_audio_data() {
    #清空语音数据
    python api_operate.py clear 4
}

function clear_content_data() {
    #清空内容数据（包含封面图链接）
    python api_operate.py clear_content
}

function gen_video() {
    arg=$1
    # 定义运行步骤
    #run_flag="content_rewrite|cover_gen|clear_audio_data|voice_gen|download_wavs|rotate_image_wav|srt_gen|srt_fix|srt_merge|add_bgm_rotate|clear_content_data"
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
    if [ "$arg" = "co" ]; then
        run_flag="content_pic_get"
    elif [ "$arg" = "re" ]; then
        run_flag="content_rewrite"
    elif [ "$arg" == "wav" ]; then
        run_flag="clear_audio_data|voice_gen|download_wavs"
    elif [ "$arg" == "sg" ]; then
        run_flag="srt_gen"
    elif [ "$arg" == "sf" ]; then
        run_flag="srt_fix"
    elif [ "$arg" == "sa" ]; then
        run_flag="srt_ass_gen"
    elif [ "$arg" == "video" ]; then
        run_flag="content_video_pic_gen|video_bg_srt_gen|video_bg_srt_ass_gen|video_bg_srt_ass_header_gen|video_add_bgm"
    else
        run_flag=$arg
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