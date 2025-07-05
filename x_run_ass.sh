# 生成ass文件
rm -f jiqimao/result_srt.ass
python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red

# 用新字体生成mp4字幕文件
rm -f output.mp4
#ffmpeg -i jiqimao/result_video_rotate.mp4 -vf "ass=jiqimao/result_srt.ass" -c:a copy output.mp4
ffmpeg -i jiqimao/result_video_rotate.mp4 -vf "ass=jiqimao/result_srt.ass:fontsdir=./font" -c:a copy output.mp4

# 添加水印
rm -f out1.mp4
ffmpeg -i output.mp4 -vf "drawtext=text='@版权所有':fontfile=./font/鸿雷板书简体-正式版.ttf:fontsize=36:fontcolor=white:x=W-tw-10:y=10" out1.mp4
