source x_run_common.sh

function merge() {
    final_video=tmp/0_merged_cover.mp4
    bgm_video=tmp/0_merged_cover_bgm.mp4
    bgm_file=bgm/slow/7.wav
    cover_list=tmp/cover_list.txt

    max_num=5
    rm -f $cover_list
    for((i=0;i<$max_num;i++)); do
        dir=00$i
        echo "file '$dir/x_final.mp4'" >> $cover_list
    done
    # 合并视频
    rm -f $final_video $bgm_video
    ffmpeg -f concat -safe 0 -i $cover_list -c copy $final_video
    video_add_bgm $final_video $bgm_file $bgm_video
    
    # 删除临时文件
    #rm cover_list.txt
}

function all() {
    voice=dushunan
    title="自渡"
    file_txt=ai_responses_plain.txt
    #封面视频
    #cover_srt_gen 000 "今天我们分享的是" null picture/cover_pic_heng_169.jpg white center on
    #cover_srt_gen 000 "今天我们分享的是毛姆的一篇长篇小说《${title}》" null picture/cover_pic_heng_169.jpg white center $voice srt_gen_on
    #封面视频
    #cover_srt_gen 001 "《${title}》" "《${title}》" picture/cover_pic_heng_169.jpg white bottom $voice srt_gen_on
    #cover_srt_gen 001 "毛姆的《${title}》" "《${title}》" black white bottom
    #内容页视频
    #对file_txt进行分段，一行一个文件，并且添加文件后缀
    id=1
    mkdir -p tmp
    prefix=tmp/ai_responses_plain_part_
    rm -rf $prefix*
    split_file_txt $file_txt 1 $prefix
    for file in $(ls $prefix*); do
        id=$(($id+1))
        dir_id="$(printf "%03d" $id)"
        if [ 1 -eq 1 ] && [ $id != 2 ]; then
            continue
        fi
        rm -rf $dir_id
        echo $dir_id $file
        content_video_gen $dir_id $file $file $voice
    done
}

func $1