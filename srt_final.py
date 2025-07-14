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
    with open(srt_content_file, "r", encoding="utf-8") as f:
        srt_lines = f.readlines()
        cnt = 0
        for line in srt_lines:
            if "  " in line:
                line_split = line.split("  ")
                word = line_split[1].strip()
                word = remove_punc(word)
                print(word)

def content_map(content_file):
    content_map = {}
    content_map_list = []
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
        print(" ".join(item))

if __name__ == "__main__":
    srt_file = "006/content_srt_words.txt"
    content_file = "006/content_fix.txt"

    #srt_to_content(srt_file)
    content_map(content_file)