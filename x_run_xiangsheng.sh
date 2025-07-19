source sys_common.sh
# 获取运行脚本名字
script_name=$0
dir_name=$(echo $script_name | sed 's/\.sh//' | sed 's/^x_//' | sed 's/^run_//')
echo "run: "$dir_name
base_dir=data_$dir_name

function merge() {
    bgm_file=sys_bgm/slow/7.wav
    final_video=$base_dir/final_merge.mp4
    bgm_video=$base_dir/final_merge_bgm.mp4
    video_list=$base_dir/video_list.txt

    mkdir -p $base_dir

    max_num=100
    rm -f $video_list
    for((i=0;i<$max_num;i++)); do
        dir=$base_dir/$00$i
        mp4_file=$dir/x_final.mp4
        if [ -f $mp4_file ]; then   
            echo "file '$mp4_file'" >> $video_list
        else
            break
        fi
    done
    # 合并视频
    rm -f $final_video $bgm_video
    ffmpeg -f concat -safe 0 -i $video_list -c copy $final_video
    video_add_bgm $final_video $bgm_file $bgm_video
    
    # 删除临时文件
    #rm video_list.txt
}

function all() {
    voice=guodegang
    title="一句顶一万句"
    file_txt=ai_responses_plain.txt
    #封面视频
    #cover_srt_gen 000 "今天我们分享的是" null sys_picture/cover_pic_heng_169.jpg white center on
    #cover_srt_gen $base_dir/000 "今天我们分享的是毛姆的一篇长篇小说《${title}》" null sys_picture/cover_pic_heng_169.jpg white center $voice srt_gen_on
    #封面视频
    
    #内容页视频
    #对file_txt进行分段，一行一个文件，并且添加文件后缀
    id=-1
    jump_to_id=-14
    jump_flag=jump_true
    rm_dir=rm_false
    mode=single
    mkdir -p $base_dir
    prefix=$base_dir/text_part_
    rm -rf $prefix*
    split_file_txt $file_txt 1 $prefix
    for file in $(ls $prefix*); do
        id=$(($id+1))
        if [ $jump_to_id -lt 0 ]; then
            jump_to_id_local=$((0-$jump_to_id))
            #echo "jump_to_id: $jump_to_id_local"
            if [ $mode == "preall" ] && [ $id -lt $jump_to_id_local ]; then
                continue
            fi
            if [ $mode == "single" ] && [ $id != $jump_to_id_local ]; then
                continue
            fi
        fi
        echo "id: $id"
        dir_id="$(printf "%03d" $id)"
        full_dir=$base_dir/$dir_id
        if [ $rm_dir == "rm_true" ]; then
            rm -rf $full_dir
        fi
        echo $full_dir $file
        if [ $id -eq 0 ]; then
            cover_srt_gen $full_dir $file "《${title}》" sys_picture/cover_pic1_heng_169.jpg white bottom $voice srt_gen_on
        else
            content_video_gen $full_dir $file $file $voice $jump_flag
        fi
    done
}

func $1