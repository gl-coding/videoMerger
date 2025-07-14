import os
import pypinyin

# word转换为拼音
def word_to_pinyin(word):
    return pypinyin.lazy_pinyin(word)

#去除两端的标点符号
def remove_punc(word):
    punc = "，。！？,.!?;；:：、《》“”"
    #去掉两端的标点符号
    word = word.strip(punc)
    return word

def is_punc(word):
    punc = "，。！？,.!?;；:：、》”"
    return word in punc

def is_punc_otherwise(word):
    punc = "《“"
    return word in punc

def is_all_punc(word):
    punc = "，。！？,.!?;；:：、《》“”"
    return word in punc

def srt_to_content(srt_content_file):
    result_list = []
    with open(srt_content_file, "r", encoding="utf-8") as f:
        srt_lines = f.readlines()
        cnt = 0
        for line in srt_lines:
            if "  " in line:
                line_split = line.split("  ")
                word = line_split[1].strip()
                word = remove_punc(word)
                #print(cnt, word, pypinyin.lazy_pinyin(word))
                #result_list.append((word, pypinyin.lazy_pinyin(word), cnt))
                #拆分中文字符串
                for it in word:
                    #print(it)
                    result_list.append((cnt, it, pypinyin.lazy_pinyin(it)))
                cnt += 1
    return result_list

def content_map(content_file):
    content_map_list = []
    result_list = []
    with open(content_file, "r", encoding="utf-8") as f:
        content_lines = f.readlines()
        pre_word = ""
        local_str = ""
        for line in content_lines:
            pre_word = ""
            for word in line:
                if word.strip() == "":
                    continue
                #process
                cur_word = word
                if is_punc_otherwise(pre_word):
                    local_str = pre_word + cur_word
                elif is_punc(cur_word) and not is_punc_otherwise(cur_word):
                    local_str += cur_word
                    content_map_list.pop()
                else:
                    local_str = cur_word
                clean_word = remove_punc(local_str)
                content_map_list.append([cur_word, clean_word, local_str])
                pre_word = cur_word
    for item in content_map_list:
        #print(" ".join(item))
        if item[1] != "":
            result_list.append([item[1], pypinyin.lazy_pinyin(item[1]), item[2]])
    return result_list

def line_map_new(final_map_list):
    result_list = []
    local_str = final_map_list[0][3]
    global_idx = -1
    for i in range(1, len(final_map_list)):
        pre_idx = final_map_list[i-1][0]
        idx = final_map_list[i][0]
        global_idx = idx
        if idx != pre_idx:
            print(pre_idx, local_str)
            result_list.append([global_idx, local_str])
            local_str = final_map_list[i][5]
        else:
            local_str += final_map_list[i][5]
    print(global_idx, local_str)
    result_list.append([global_idx, local_str])
    return result_list

if __name__ == "__main__":
    dir = "006"
    srt_file = dir + "/content_srt_words.txt"
    content_file = dir + "/content_fix.txt"

    content_map_list = content_map(content_file)
    srt_map_list = srt_to_content(srt_file)
    #for item in content_map_list: print(item)
    cnt = 0
    final_map_list = []
    for i in range(len(srt_map_list)):
        #print(srt_map_list[i])
        idx  = srt_map_list[i][0]
        word = srt_map_list[i][1]
        pinyin = srt_map_list[i][2]
        if cnt < len(content_map_list):
            map_word = content_map_list[cnt]
            print(idx, word, pinyin, map_word[0], map_word[1], map_word[2])
            final_map_list.append([idx, word, pinyin, map_word[0], map_word[1], map_word[2]])
            cnt += 1
        else:
            print(idx, word, pinyin, "None", "None", "None")
            final_map_list.append([idx, word, pinyin, "None", "None", "None"])
            cnt += 1
    line_map_new(final_map_list)
