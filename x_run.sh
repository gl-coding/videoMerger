data_dir=data
voice=jiqimao
filename=$data_dir/$voice
tmp_file=$data_dir/tmp.mp4
content_pic=$filename.jpeg
local_pic=picture/doutu/001.jpg

rm -f $tmp_file

function content_pic_gen() {
    #内容图片生成
    python content_pic_gen.py $local_pic --padding 100 -o $content_pic
}

function content_rewrite() {
    #文案获取
    python coze_content_rewrite.py $data_dir
}

function cover_gen() {
    #封面生成
    python coze_cover_gen.py $data_dir
}

function voice_gen() {
    #语音生成
    python clone_voice.py -f $content_pic -o $voice -v $voice
}

function download_wavs() {
    #下载语音
    python download_wavs.py 4 --delete-after-download -d data/
}

function video_merger() {
    #视频合成
    python video_merger.py $filename.jpeg $filename.wav $tmp_file
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
run_flag="content_pic_gen"

# 方法1: 使用 tr 命令分割字符串并打印
echo "$run_flag" | tr '|' '\n' | while read -r step; do
    echo "步骤: $step"
    $step
done
