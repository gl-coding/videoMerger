data_dir=jiqimao_`date +%Y%m%d%H%M`
voice=jiqimao
filename=$data_dir/$voice
content_file=$filename.txt
title_file=$data_dir/$voice"_title.txt"
subtitle_file=$data_dir/$voice"_subtitle.txt"
tmp_file=$data_dir/tmp.mp4
content_pic=$filename.jpeg
content_video=$filename.mp4
local_pic=picture/doutu/001.jpg
uuid=$voice
voice_file=$data_dir/$uuid.wav

rm -rf $tmp_file $data_dir
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
    python fix_srt.py $filename.txt $filename.srt -o ${filename}_corrected.srt
}

function srt_merge() {
    #字幕合成
    rm -f $filename.mp4
    ffmpeg -i $tmp_file -vf "subtitles=${filename}_corrected.srt:force_style='FontSize=25'" $filename.mp4
}

function delete_api_data() {
    #上传视频
    python upload.py
}

function gen_video() {
    # 定义运行步骤
    run_flag="content_pic_gen|content_rewrite|cover_gen|voice_gen|download_wavs|video_merger|srt_gen|srt_fix|srt_merge"
    #run_flag="content_pic_gen"
    #run_flag="content_rewrite"
    #run_flag="cover_gen"
    #run_flag="voice_gen"
    #run_flag="download_wavs"
    #run_flag="video_merger"
    #run_flag="srt_gen"
    #run_flag="srt_fix"
    #run_flag="srt_merge"

    # 方法1: 使用 tr 命令分割字符串并打印
    echo "$run_flag" | tr '|' '\n' | while read -r step; do
        echo "\n=============================================="
        echo "步骤: $step"
        $step
    done
}

case $1 in
    gen_video)
        gen_video
        ;;
    delete_api_data)
        delete_api_data
        ;;
    *)
        echo "Usage: $0 {gen_video|delete_api_data}"
        exit 1
esac

#sh x_run.sh gen_video