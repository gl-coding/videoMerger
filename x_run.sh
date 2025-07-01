data_dir=jiqimao_`date +%Y%m%d%H%M`
#data_dir=jiqimao_202506302254
voice=jiqimao
filename=$data_dir/$voice
content_file=$filename.txt
title_file=$data_dir/$voice"_title.txt"
subtitle_file=$data_dir/$voice"_subtitle.txt"
tmp_file=$data_dir/tmp.mp4
content_pic=$filename.jpeg
content_video=$filename.mp4
content_video_bgm=$filename"_bgm.mp4"
content_video_rotate=$filename"_rotate.mp4"
content_video_srt=$filename"_srt.mp4"
content_video_final=$filename"_final.mp4"
content_video_bgm_rotate=$filename"_bgm_rotate.mp4"
local_pic=picture/doutu/001.jpg
uuid=$voice
voice_file=$data_dir/$uuid.wav
bgm_file=bgm/1.wav

#rm -rf $tmp_file $data_dir
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
    sh rotate_image_wav.sh -w 1024 -h 574 -z 2 -p 50 $content_pic $voice_file $content_video_rotate
}

function video_merger() {
    #视频合成
    python video_merger.py $content_pic $voice_file $tmp_file
}

function srt_gen() {
    #语音转字幕
    rm -f $filename.srt
    python srt_gen.py $filename.wav $filename.srt
}

function srt_fix() {
    #字幕纠错
    if [ ! -f $filename.srt ]; then
        echo "字幕文件不存在，exit"
        exit 1
    fi
    python fix_srt.py $filename.txt $filename.srt -o ${filename}_corrected.srt
}

function srt_merge() {
    #字幕合成
    rm -f $content_video_srt
    ffmpeg -i $content_video_rotate -vf "subtitles=${filename}_corrected.srt:force_style='FontSize=25'" $content_video_srt
}

function add_bgm() {
    # 循环背景音乐，音量20%，3秒淡入淡出
    ./add_bgm.sh -v 0.3 -l -f 1 -F 1 $content_video_srt $bgm_file $content_video_bgm
}

function add_bgm_rotate() {
    # 循环背景音乐，音量20%，3秒淡入淡出
    sh add_bgm.sh -v 0.3 -l -f 1 -F 1 $content_video_srt $bgm_file $content_video_bgm_rotate
}

function delete_api_data() {
    #上传视频
    python upload.py
}

function gen_video() {
    arg=$1
    # 定义运行步骤
    run_flag="content_rewrite|cover_gen|voice_gen|download_wavs|rotate_image_wav|srt_gen|srt_fix|srt_merge|add_bgm_rotate"
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
    delete)
        delete_api_data
        ;;
    *)
        echo "Usage: $0 {gen|delete}"
        exit 1
esac

#sh x_run.sh gen re
#sh x_run.sh gen all