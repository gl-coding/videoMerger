filename=data/qinghuanv
tmp_file=data/tmp.mp4

#视频合成
python video_merger.py $filename.jpeg $filename.wav $tmp_file

#语音转字幕
python srt_gen.py $filename.wav $filename.srt

#字幕合成
ffmpeg -i $tmp_file -vf "subtitles=$filename.srt" $filename.mp4

rm $tmp_file