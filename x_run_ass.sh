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
python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 120 --color white  --highlight --keyword-size 160 --per-line --dict-file jiqimao/dict.txt --skip-lines "1,2" --effects "fade,move_right,move_left"
#python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect rotate
#python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect shake
#python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect wave
#python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect bounce
#python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect move_up
#python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect move_down
#python3 srt2ass_with_effect.py jiqimao/result_srt.srt jiqimao/result_srt.ass --align 5 --font "鸿雷板书简体-正式版" --size 136 --color red --effect move_right

# 用新字体生成mp4字幕文件
rm -f output.mp4
#ffmpeg -i jiqimao/result_video_rotate.mp4 -vf "ass=jiqimao/result_srt.ass" -c:a copy output.mp4
ffmpeg -i jiqimao/result_video_rotate.mp4 -vf "ass=jiqimao/result_srt.ass:fontsdir=./font" -c:a copy output.mp4

# 添加水印
rm -f out1.mp4
ffmpeg -i output.mp4 -vf "drawtext=text='@版权所有':fontfile=./font/鸿雷板书简体-正式版.ttf:fontsize=36:fontcolor=white:x=W-tw-10:y=10" out1.mp4
