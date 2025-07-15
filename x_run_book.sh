data_dir=jiqimao
voice=dushunan
name=kumi的读书日记
filename=$data_dir/result

#cover
content_pic=$data_dir/pic_cover_0.jpg
line_max_chars=15
ass_font_size=120

#wav
uuid=result
voice_file=$data_dir/$uuid.wav
bgm_file=bgm/slow/7.wav

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
    local_dir=$1
    local_title_file=$2
    python3 coze_content_pic_gen.py $local_dir "$(cat $local_title_file)"
}

function content_fix() {
    local_content_file=$1
    local_content_file_fix=$2
    python remove_ending_numbers.py $local_content_file $local_content_file_fix
}

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
    dir=$2
    name=$2
    wavfile=$dir/result.wav
    text_file=$dir/$name.txt

    mkdir -p $dir
    if [ -f $text ]; then
        cp $text $text_file
    else
        echo $text > $text_file
    fi
    #提交语音生成任务
    python clone_voice.py -f $text_file -o $uuid -v $voice
    #下载语音
    rm -f $wavfile
    while true; do
        if [ ! -f $wavfile ]; then
            python download_wavs.py 4 --delete-after-download -d $dir
        else
            echo "语音文件已存在"
            break
        fi
        sleep 10
    done
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
    title=$3
    bg_color=$4
    font_color=$5
    pos=$6

    echo "cover_srt_gen $dir $text $bg_color $font_color $pos"
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
    cover_voice_srt_final=$cover_pic_dir/cover_voice_srt_final.srt

    mkdir -p $cover_pic_dir

    #生成语音
    cover_voice_gen $text $cover_pic_dir
    #生成字幕
    rm -f $cover_voice_srt
    #python srt_gen.py $cover_voice_file $cover_voice_srt 
    #srt_gen $cover_voice_file $cover_voice_srt_words $cover_voice_srt_final
    srt_gen $cover_voice_file $cover_voice_srt $cover_voice_srt_words $cover_voice_srt_final
    if [ $bg_color != "black" ]; then
        echo "图片背景视频"
        if [ -f $bg_color ]; then
            cp $bg_color $cover_pic_text_first
            #生成图片视频
            rm -f $cover_pic_video
            #sh image_to_video.sh $cover_pic_text_first $cover_voice_file $cover_pic_video -e zoom_in -s 2.0 --final-zoom 2.0
            sh image_to_video.sh $cover_pic_text_first $cover_voice_file $cover_pic_video -e null
        else
            echo "图片不存在，使用黑色背景图片"
            rm -f $cover_pic_video
            sh image_to_video.sh --color-only -b black $cover_voice_file $cover_pic_video
        fi
    else
        echo "纯色背景视频"
        rm -f $cover_pic_video
        sh image_to_video.sh --color-only -b black $cover_voice_file $cover_pic_video
    fi

    #字幕校验
    echo $text > $cover_text
    srt_fix $cover_voice_srt_final $cover_text $cover_voice_srt_correct $cover_voice_srt_correct_merge
    #生成ass文件
    if [ $pos == "center" ]; then
        align=5
    elif [ $pos == "bottom" ]; then
        align=2
    else
        align=8
    fi
    rm -f $cover_voice_srt_ass
    #python3 srt2ass_with_effect.py $cover_voice_srt $cover_voice_srt_ass --align 2 --font "鸿雷板书简体-正式版" --size 120 --color white  
    # python3 srt2ass_with_effect.py $cover_voice_srt_correct $cover_voice_srt_ass --align $align \
    #     --font "鸿雷板书简体-正式版" --size 120 --color $font_color --effect typewriter --max-chars 5
    python3 srt2ass_with_effect.py $cover_voice_srt_correct_merge $cover_voice_srt_ass --align $align \
        --font "鸿雷板书简体-正式版" --size $ass_font_size --color $font_color --max-chars $line_max_chars
    #mp4合并ass
    rm -f $cover_video_ass
    ffmpeg -i $cover_pic_video -vf "ass=$cover_voice_srt_ass:fontsdir=./font" -c:a copy $cover_video_ass

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
    sh image_to_video.sh $local_pic $local_voice_file $local_content_video -e null
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
    python srt_gen.py $local_voice $local_srt large-v3 zh $local_srt_words
    #python srt_punc_map.py $local_content $local_srt_words $local_srt_words_punc
    python srt_final.py $local_content $local_srt_words $local_srt_words_punc
    python srt_gen_fromwords.py $local_srt_words_punc $local_srt_final
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
    python fix_srt.py $local_srt $local_content -o $local_correct_srt
    python3 srt_merge.py $local_correct_srt $local_correct_srt_merge
}

function srt_ass_gen() {
    local_correct_srt=$1
    local_srt_ass=$2
    python3 srt2ass_with_effect.py  --align 5 --font "鸿雷板书简体-正式版" --size $ass_font_size --color red $local_correct_srt $local_srt_ass --max-chars $line_max_chars
}

# 添加背景文字（可选）
function video_bg_srt_gen() {
    local_video=$1
    local_title=$2
    local_video_bg_srt=$3
    rm -f $local_video_bg_srt
    ffmpeg -i $local_video -vf "drawtext=text='$local_title':fontfile=./font/Aa剑豪体.ttf:fontsize=160:fontcolor=red@0.8:x=(W-tw)/2:y=100:" $local_video_bg_srt
}

# 用新字体生成mp4字幕文件
function gen_ass_video() {
    local_srt_video=$1
    local_ass_file=$2
    local_ass_video=$3
    rm -f $local_ass_video
    #ffmpeg -i jiqimao/result_video_rotate.mp4 -vf "ass=jiqimao/result_srt.ass" -c:a copy output.mp4
    ffmpeg -i $local_srt_video -vf "ass=$local_ass_file:fontsdir=./font" -c:a copy $local_ass_video
}

# 视频添加水印
function video_add_watermark() {
    local_name=$1
    local_video=$2
    local_video_pre_header=$local_video"_pre_watermark.mp4"
    rm -f $local_video_pre_header
    ffmpeg -i $local_video -vf "drawtext=text='@$local_name':fontfile=./font/鸿雷板书简体-正式版.ttf:fontsize=36:fontcolor=white:x=10:y=10" $local_video_pre_header

    if [ "" = "null" ]; then
        local_video_post_header=$local_video"_post_watermark.mp4"
        rm -f $local_video_post_header
        #ffmpeg -i $local_video_pre_header -vf "drawtext=text='@版权所有':fontfile=./font/鸿雷板书简体-正式版.ttf:fontsize=36:fontcolor=white@0.8:x=W-tw-10:y=10:shadowcolor=black:shadowx=2:shadowy=2" $local_video_post_header
        ffmpeg -i $local_video_pre_header -vf "drawtext=text='@$local_name':fontfile=./font/鸿雷板书简体-正式版.ttf:fontsize=36:fontcolor=white:x=W-tw-10:y=10" $local_video_post_header
    fi 
}

function content_video_gen() {
    local_dir=$1
    local_title=$2
    local_content_file=$3
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
    if [ $local_title != "null" ]; then
        echo $local_title > $pic_content_file
    fi
    content_pic_get $local_dir $pic_content_file
    #生成语音
    echo "我步入丛林，因为我希望生活得有意义……以免在临终时，发现自己从来没有活过。" > $content_file
    if [ -f $local_content_file ]; then
        cp $local_content_file $content_file
    fi
    #原文纠错（去引用）
    content_fix $content_file $content_file_fix
    #语音生成
    #cover_voice_gen "$(cat $content_file)" $dir
    cover_voice_gen $content_file_fix $local_dir
    #生成视频
    content_video_pic_gen $content_pic $content_voice_file $content_video
    #生成字幕
    srt_gen $content_file_fix $content_voice_file $content_srt $content_srt_words $content_srt_words_punc $content_srt_final
    #字幕纠错
    srt_fix  $content_srt_final $content_file_fix $content_correct_srt $content_correct_srt_merge
    #字幕转ass
    srt_ass_gen $content_correct_srt_merge $content_correct_ass
    #生成带ass字幕的视频
    gen_ass_video $content_video $content_correct_ass $content_video_ass
    #生成最终视频
    cp  $content_video_ass $local_dir/x_final.mp4
}

#整体添加bgm
function video_add_bgm() {
    local_video=$1
    local_bgm_video=$2
    # 循环背景音乐，音量20%，3秒淡入淡出
    rm -f $local_bgm_video
    sh add_bgm.sh -v 0.4 -l -f 1 -F 1 $local_video $bgm_file $local_bgm_video
}

function merge_cover_video_all() {
    final_video=0_merged_cover.mp4
    bgm_video=0_merged_cover_bgm.mp4

    max_num=$(($1+1))
    rm -f cover_list.txt
    for((i=0;i<$max_num;i++)); do
        dir=00$i
        echo "file '$dir/x_final.mp4'" >> cover_list.txt
    done
    # 合并视频
    rm -f $final_video $bgm_video
    ffmpeg -f concat -safe 0 -i cover_list.txt -c copy $final_video
    video_add_bgm $final_video $bgm_video
    
    # 删除临时文件
    rm cover_list.txt
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
        content_video_gen 002 "$title" $file_txt
        mv $file_md ai_responses/
        break
    done
}

function content_video_gen_all() {
    title="习得性无助"
    file_txt=ai_responses_plain.txt
    #封面视频
    #cover_srt_gen 000 "今天我们分享的是" null picture/cover_pic_heng_169.jpg white center
    #cover_srt_gen 000 "今天我们分享的是毛姆的一篇长篇小说《${title}》" null picture/cover_pic_heng_169.jpg white center
    #封面视频
    #cover_srt_gen 001 "毛姆的《${title}》" "《${title}》" picture/cover_pic_heng_169.jpg white bottom
    #cover_srt_gen 001 "毛姆的《${title}》" "《${title}》" black white bottom
    #内容页视频
    #对file_txt进行分段，一行一个文件，并且添加文件后缀
    id=1
    prefix=ai_responses_plain_part_
    split_file_txt $file_txt 1 $prefix
    for file in $(ls $prefix*); do
        dir_id="$(printf "%03d" $(($id+1)))"
        id=$(($id+1))
        if [ 1 -eq 1 ] && [ $id != 2 ]; then
            continue
        fi
        echo $dir_id $file
        content_video_gen $dir_id "${title}" $file
    done
    #merge_cover_video_all  2
}

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