#cover srt
line_max_chars=15
ass_font_size=120

# 获取内容图片
function content_pic_get() {
    local_dir=$1
    local_title_file=$2
    python libpy/coze_content_pic_gen.py $local_dir "$(cat $local_title_file)"
}

function content_fix() {
    local_content_file=$1
    local_content_file_fix=$2
    python libpy/remove_ending_numbers.py $local_content_file $local_content_file_fix
}

# 提交获取语音任务
function voice_gen() {
    clear_audio_data
    text=$1
    dir=$2
    voice=$3
    wavfile=$dir/result.wav
    text_file=$dir/result.txt

    mkdir -p $dir
    if [ -f $text ]; then
        cp $text $text_file
    else
        echo $text > $text_file
    fi
    #提交语音生成任务
    uuid=result
    python libpy/clone_voice.py -f $text_file -o $uuid -v $voice
    #下载语音
    rm -f $wavfile
    while true; do
        if [ ! -f $wavfile ]; then
            python libpy/download_wavs.py 4 --delete-after-download -d $dir
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
    title=$3
    bg_color=$4
    font_color=$5
    srt_pos=$6
    voice=$7
    srt_flag=$8

    echo "cover_srt_gen $dir $text $bg_color $font_color $srt_pos"
    cover_pic_dir=$dir
    cover_pic=$cover_pic_dir/cover_pic.jpg
    cover_text=$cover_pic_dir/cover_text.txt
    cover_pic_text=$cover_pic_dir/cover_pic_text.jpg
    cover_pic_first=$cover_pic_dir/cover_pic_first.jpg
    cover_pic_text_first=$cover_pic_dir/cover_pic_text_first.jpg
    cover_pic_video=$cover_pic_dir/cover_pic_video.mp4
    cover_video_ass=$cover_pic_dir/cover_video_ass.mp4
    cover_video_bg_srt=$cover_pic_dir/cover_video_bg_srt.mp4
    cover_voice_file=$cover_pic_dir/result.wav
    cover_voice_srt=$cover_pic_dir/cover_voice_srt.srt
    cover_voice_srt_correct=$cover_pic_dir/cover_voice_srt_corrected.srt
    cover_voice_srt_correct_merge=$cover_pic_dir/cover_voice_srt_corrected_merge.srt
    cover_voice_srt_ass=$cover_pic_dir/cover_voice_srt_ass.ass
    cover_video_wav=$cover_pic_dir/cover_video_wav.mp3
    cover_voice_srt_words=$cover_pic_dir/cover_voice_srt_words.txt
    cover_voice_srt_words_punc=$cover_pic_dir/cover_voice_srt_words_punc.txt
    cover_voice_srt_final=$cover_pic_dir/cover_voice_srt_final.srt

    mkdir -p $cover_pic_dir

    #生成语音
    voice_gen $text $cover_pic_dir $voice
    #生成字幕
    rm -f $cover_voice_srt
    #python srt_gen.py $cover_voice_file $cover_voice_srt 
    #srt_gen $cover_voice_file $cover_voice_srt_words $cover_voice_srt_final
    if [ -f $text ]; then
        cp $text $cover_text
    else
        echo $text > $cover_text
    fi
    if [ $srt_flag == "srt_gen_on" ]; then
        srt_gen $cover_text $cover_voice_file $cover_voice_srt $cover_voice_srt_words $cover_voice_srt_words_punc $cover_voice_srt_final
    fi
    #srt_gen $content_file_fix $content_voice_file $content_srt $content_srt_words $content_srt_words_punc $content_srt_final
    if [ $bg_color != "black" ]; then
        echo "图片背景视频"
        if [ -f $bg_color ]; then
            cp $bg_color $cover_pic_text_first
            #生成图片视频
            rm -f $cover_pic_video
            #sh image_to_video.sh $cover_pic_text_first $cover_voice_file $cover_pic_video -e zoom_in -s 2.0 --final-zoom 2.0
            sh libsh/image_to_video.sh $cover_pic_text_first $cover_voice_file $cover_pic_video -e null
        else
            echo "图片不存在，使用黑色背景图片"
            rm -f $cover_pic_video
            sh libsh/image_to_video.sh --color-only -b black $cover_voice_file $cover_pic_video
        fi
    else
        echo "纯色背景视频"
        rm -f $cover_pic_video
        sh libsh/image_to_video.sh --color-only -b black $cover_voice_file $cover_pic_video
    fi

    #字幕校验
    #echo $text > $cover_text
    #srt_fix $cover_voice_srt_final $cover_text $cover_voice_srt_correct $cover_voice_srt_correct_merge
    #生成ass文件
    if [ $srt_pos == "center" ]; then
        align=5
    elif [ $srt_pos == "bottom" ]; then
        align=2
    else
        align=8
    fi
    rm -f $cover_voice_srt_ass
    #python3 srt2ass_with_effect.py $cover_voice_srt $cover_voice_srt_ass --align 2 --font "鸿雷板书简体-正式版" --size 120 --color white  
    # python3 srt2ass_with_effect.py $cover_voice_srt_correct $cover_voice_srt_ass --align $align \
    #     --font "鸿雷板书简体-正式版" --size 120 --color $font_color --effect typewriter --max-chars 5
    python libpy/srt2ass_with_effect.py $cover_voice_srt_final $cover_voice_srt_ass --align $align \
        --font "鸿雷板书简体-正式版" --size $ass_font_size --color $font_color --max-chars $line_max_chars
    #mp4合并ass
    rm -f $cover_video_ass
    ffmpeg -i $cover_pic_video -vf "ass=$cover_voice_srt_ass:fontsdir=./sys_font" -c:a copy $cover_video_ass

    #是否在最终的视频上添加大字背景
    if [ $title != "null" ]; then
        video_bg_srt_gen $cover_video_ass $title $cover_video_bg_srt
        cp $cover_video_bg_srt $cover_pic_dir/x_final.mp4
    else
        cp $cover_video_ass $cover_pic_dir/x_final.mp4
    fi
}

function content_video_pic_gen() {
    local_pic=$1
    local_voice_file=$2
    local_content_video=$3
    rm -f $local_content_video
    #sh image_to_video.sh $local_pic $local_voice_file $local_content_video -e kenburns
    #sh image_to_video.sh $local_pic $local_voice_file $local_content_video -e fade
    #sh image_to_video.sh $local_pic $local_voice_file $local_content_video -e move_down
    sh libsh/image_to_video.sh $local_pic $local_voice_file $local_content_video -e null
}

#content_video_pic_gen

function srt_gen() {
    #语音转字幕
    local_content=$1
    local_voice=$2
    local_srt=$3
    local_srt_words=$4
    local_srt_words_punc=$5
    local_srt_final=$6
    rm -f $local_srt $local_srt_words $local_srt_final
    python libpy/srt_gen.py $local_voice $local_srt large-v3 zh $local_srt_words
    #python srt_punc_map.py $local_content $local_srt_words $local_srt_words_punc
    python libpy/srt_final.py $local_content $local_srt_words $local_srt_words_punc
    python libpy/srt_gen_fromwords.py $local_srt_words_punc $local_srt_final
}

function srt_fix() {
    #字幕纠错
    local_srt=$1
    local_content=$2
    local_correct_srt=$3
    local_correct_srt_merge=$4
    if [ ! -f $local_srt ]; then
        echo "字幕文件不存在，exit"
        exit 1
    fi
    rm -f $local_correct_srt $local_correct_srt_merge
    python libpy/fix_srt.py $local_srt $local_content -o $local_correct_srt
    python libpy/srt_merge.py $local_correct_srt
}

function srt_ass_gen() {
    local_correct_srt=$1
    local_srt_ass=$2
    python libpy/srt2ass_with_effect.py  --align 5 --font "鸿雷板书简体-正式版" --size $ass_font_size \
        --color red $local_correct_srt $local_srt_ass --max-chars $line_max_chars
}

# 添加背景文字（可选）
function video_bg_srt_gen() {
    local_video=$1
    local_title=$2
    local_video_bg_srt=$3
    rm -f $local_video_bg_srt
    ffmpeg -i $local_video -vf "drawtext=text='$local_title':fontfile=./sys_font/Aa剑豪体.ttf:fontsize=160:fontcolor=red@0.8:x=(W-tw)/2:y=100:" $local_video_bg_srt
}

# 用新字体生成mp4字幕文件
function gen_ass_video() {
    local_srt_video=$1
    local_ass_file=$2
    local_ass_video=$3
    rm -f $local_ass_video
    #ffmpeg -i jiqimao/result_video_rotate.mp4 -vf "ass=jiqimao/result_srt.ass" -c:a copy output.mp4
    ffmpeg -i $local_srt_video -vf "ass=$local_ass_file:fontsdir=./sys_font" -c:a copy $local_ass_video
}

# 视频添加水印
function video_add_watermark() {
    local_name=$1
    local_video=$2
    local_video_pre_header=$local_video"_pre_watermark.mp4"
    rm -f $local_video_pre_header
    ffmpeg -i $local_video -vf "drawtext=text='@$local_name':fontfile=./sys_font/鸿雷板书简体-正式版.ttf:fontsize=36:fontcolor=white:x=10:y=10" $local_video_pre_header

    if [ "" = "null" ]; then
        local_video_post_header=$local_video"_post_watermark.mp4"
        rm -f $local_video_post_header
        #ffmpeg -i $local_video_pre_header -vf "drawtext=text='@版权所有':fontfile=./font/鸿雷板书简体-正式版.ttf:fontsize=36:fontcolor=white@0.8:x=W-tw-10:y=10:shadowcolor=black:shadowx=2:shadowy=2" $local_video_post_header
        ffmpeg -i $local_video_pre_header -vf "drawtext=text='@$local_name':fontfile=./sys_font/鸿雷板书简体-正式版.ttf:fontsize=36:fontcolor=white:x=W-tw-10:y=10" $local_video_post_header
    fi 
}

function content_video_gen() {
    local_dir=$1
    local_title=$2
    local_content_file=$3
    voice=$4
    pic_content_file=$local_dir/pic_content.txt
    content_file=$local_dir/content.txt
    content_file_fix=$local_dir/content_fix.txt
    content_video=$local_dir/video.mp4
    content_video_ass=$local_dir/video_ass.mp4
    content_voice_file=$local_dir/result.wav
    content_srt=$local_dir/content.srt
    content_srt_words=$local_dir/content_srt_words.txt
    content_srt_words_punc=$local_dir/content_srt_words_punc.txt
    content_srt_final=$local_dir/content_srt_final.srt
    content_correct_srt=$local_dir/content_corrected.srt
    content_correct_srt_merge=$local_dir/content_corrected_merge.srt
    content_correct_ass=$local_dir/content_corrected.ass
    content_pic=$local_dir/pic_cover_0.jpg

    mkdir -p $local_dir

    #生成内容图
    if [ -f $local_title ]; then
        cp $local_title $pic_content_file
    else
        echo $local_title > $pic_content_file
    fi
    content_pic_get $local_dir $pic_content_file
    #如果内容图不存在，则退出
    if [ ! -f $content_pic ]; then
        echo "图片文件下载失败，exit"
        exit 1
    fi
    #生成语音
    echo "我步入丛林，因为我希望生活得有意义……以免在临终时，发现自己从来没有活过。" > $content_file
    if [ -f $local_content_file ]; then
        cp $local_content_file $content_file
    fi
    #原文纠错（去引用）
    content_fix $content_file $content_file_fix
    #语音生成
    #cover_voice_gen "$(cat $content_file)" $dir
    voice_gen $content_file_fix $local_dir $voice
    #生成视频
    content_video_pic_gen $content_pic $content_voice_file $content_video
    #生成字幕
    srt_gen $content_file_fix $content_voice_file $content_srt $content_srt_words $content_srt_words_punc $content_srt_final
    #字幕纠错
    #srt_fix  $content_srt_final $content_file_fix $content_correct_srt $content_correct_srt_merge
    #字幕转ass
    #srt_ass_gen $content_correct_srt_merge $content_correct_ass
    srt_ass_gen $content_srt_final $content_correct_ass
    #生成带ass字幕的视频
    gen_ass_video $content_video $content_correct_ass $content_video_ass
    #生成最终视频
    cp  $content_video_ass $local_dir/x_final.mp4
}

#整体添加bgm
function video_add_bgm() {
    local_video=$1
    local_bgm_file=$2
    local_bgm_video=$2
    # 循环背景音乐，音量20%，3秒淡入淡出
    rm -f $local_bgm_video
    sh libsh/add_bgm.sh -v 0.4 -l -f 1 -F 1 $local_video $local_bgm_file $local_bgm_video
}

function split_file_txt() {
    local_file_txt=$1
    line_num=$2
    prefix=$3
    #对file_txt进行分段，一行一个文件，并且添加文件后缀
    split -l $line_num $local_file_txt $prefix
}

function ds() {
    mkdir -p ai_responses_tmp ai_responses
    for file in $(ls ai_responses_tmp/*.md); do
        echo $file
        file_md=$file
        file_txt=ai_responses_plain.txt
        pandoc -f markdown -t plain $file_md -o $file_txt
        content_video_gen 002 "$title" $file_txt $voice
        mv $file_md ai_responses/
        break
    done
}

function clear_audio_data() {
    #清空语音数据
    python libpy/api_operate.py clear 4
}

function clear_content_data() {
    #清空内容数据（包含封面图链接）
    python libpy/api_operate.py clear_content
}

function func() {
    arg=$1
    run_flag=$arg
    # 使用数组方式分割字符串
    IFS='|' read -ra STEPS <<< "$run_flag"
    for step in "${STEPS[@]}"; do
        echo "======================================================================================="
        echo "步骤: $step"
        $step
    done
}
