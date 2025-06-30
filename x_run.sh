data_dir=jiqimao
voice=jiqimao
filename=$data_dir/$voice
tmp_file=$data_dir/tmp.mp4
content_pic=$filename.jpeg
content_video=$filename.mp4
content_file=$data_dir/content.txt
local_pic=picture/doutu/001.jpg
uuid=jiqimao
voice_file=$data_dir/$uuid.wav

#rm -rf $tmp_file $data_dir
mkdir -p $data_dir

function content_pic_gen() {
    #内容图片生成
    python content_pic_gen.py $local_pic --padding 100 -o $content_pic
}

function content_rewrite() {
    #文案获取
    python coze_content_rewrite.py $content_file
}

function cover_gen() {
    #封面生成
    python coze_cover_gen.py $data_dir "理财方法" "真相解密"
}

function voice_gen() {
    #提交语音生成任务
    python clone_voice.py -f $content_file -o $uuid -v $voice
}

function download_wavs() {
    #下载语音
    while true; do
        if [ -f $voice_file ]; then
            python download_wavs.py 4 --delete-after-download -d $data_dir
            break
        fi
        sleep 1
    done
}

function video_merger() {
    #视频合成
    python video_merger.py $content_pic $voice_file $tmp_file
}

function srt_gen() {
    #语音转字幕
    rm $filename.srt
    python srt_gen.py $filename.wav $filename.srt
}

function srt_merge() {
    #字幕合成
    rm $filename.mp4
    ffmpeg -i $tmp_file -vf "subtitles=$filename.srt:force_style='FontSize=25" $filename.mp4
}

# 定义运行步骤
#run_flag="content_pic_gen|content_rewrite|cover_gen|voice_gen|download_wavs|video_merger|srt_gen|srt_merge"
#run_flag="content_pic_gen"
#run_flag="content_rewrite"
#run_flag="cover_gen"
#run_flag="voice_gen"
#run_flag="download_wavs"
#run_flag="video_merger"
#run_flag="srt_gen"
run_flag="srt_merge"

# 方法1: 使用 tr 命令分割字符串并打印
echo "$run_flag" | tr '|' '\n' | while read -r step; do
    echo "步骤: $step"
    $step
done
