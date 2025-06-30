filename=data/qinghuanv
tmp_file=data/tmp.mp4

#封面生成
python coze_cover_gen.py

#图片生成
python content_pic_gen.py picture/doutu/001.jpg --padding 100 -o content_pic.jpg
mv content_pic.jpg $filename.jpeg

#语音生成
python clone_voice.py -f content.txt -o qinghuanv -v qinghuanv

#视频合成
python video_merger.py $filename.jpeg $filename.wav $tmp_file

#语音转字幕
rm $filename.srt
python srt_gen.py $filename.wav $filename.srt

#字幕合成
rm $filename.mp4
ffmpeg -i $tmp_file -vf "subtitles=$filename.srt:force_style='FontSize=25" $filename.mp4

rm $tmp_file