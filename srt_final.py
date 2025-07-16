import os
import sys
import pypinyin

pre_punc = "《“"
post_punc = "，。！？,.!?;；:：、》”"
all_punc = pre_punc + post_punc

# word转换为拼音
def word_to_pinyin(word):
    return pypinyin.lazy_pinyin(word)

#去除word两端的所有标点符号
def remove_all_punc(word):
    word = word.strip(all_punc)
    return word

#判断word是否为后缀标点符号
def is_post_punc(word):
    return word in post_punc

#判断word是否为前缀标点符号
def is_pre_punc(word):
    return word in pre_punc

#判断word是否为标点符号
def is_all_punc(word):
    return word in all_punc

def srt_to_content(srt_content_file):
    result_list = []
    with open(srt_content_file, "r", encoding="utf-8") as f:
        srt_lines = f.readlines()
        cnt = 0
        for line in srt_lines:
            if "  " in line:
                line_split = line.split("  ")
                word = line_split[1].strip()
                word = remove_all_punc(word)
                #print(cnt, word, pypinyin.lazy_pinyin(word))
                #result_list.append((word, pypinyin.lazy_pinyin(word), cnt))
                #拆分中文字符串
                for it in word:
                    #print(it)
                    result_list.append((cnt, it, pypinyin.lazy_pinyin(it)))
                cnt += 1
    return result_list

def gen_content_map(content_file):
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
                if is_pre_punc(pre_word):
                    local_str = pre_word + cur_word
                elif is_post_punc(cur_word) and not is_pre_punc(cur_word):
                    local_str += cur_word
                    content_map_list.pop()
                else:
                    local_str = cur_word
                clean_word = remove_all_punc(local_str)
                content_map_list.append([cur_word, clean_word, local_str])
                pre_word = cur_word
    for item in content_map_list:
        #print(" ".join(item))
        if item[1] != "":
            result_list.append([item[1], pypinyin.lazy_pinyin(item[1]), item[2]])
    return result_list

#对其srt文件
def srt_content_align(srt_map_list, content_map_list):
    final_map_list = []
    cnt = 0
    for i in range(len(srt_map_list)):
        #print(srt_map_list[i])
        idx  = srt_map_list[i][0]
        word = srt_map_list[i][1]
        pinyin = srt_map_list[i][2]
        if cnt < len(content_map_list):
            map_word = content_map_list[cnt]
            item = [idx, word, pinyin, map_word[0], map_word[1], map_word[2]]
            final_map_list.append(item)
            print(item)
            cnt += 1
        else:
            item = [idx, word, pinyin, ["None"], ["None"], ["None"]]  
            final_map_list.append(item)
            print(item)
            cnt += 1
    #similarity_check(final_map_list)
    return final_map_list

def similarity_check(final_map_list):
    item_list = [it for item in final_map_list for it in item[2]]
    item_list_txt = [it for item in final_map_list for it in item[4]]
    print(item_list)
    print(item_list_txt)

def srt_content_map(final_map_list):
    result_list = {}
    local_str = final_map_list[0][3]
    global_idx = -1
    for i in range(1, len(final_map_list)):
        pre_idx = final_map_list[i-1][0]
        idx = final_map_list[i][0]
        global_idx = idx
        if idx != pre_idx:
            print(pre_idx, local_str)
            result_list[pre_idx] = local_str
            local_str = final_map_list[i][5]
        else:
            local_str += final_map_list[i][5]
    print(global_idx, local_str)
    result_list[global_idx] = local_str
    return result_list

def srt_replace(srt_content_file, replace_map, srt_content_file_new):
    srt_lines_new = []
    with open(srt_content_file, "r", encoding="utf-8") as f:
        srt_lines = f.readlines()
        idx = 0
        for line in srt_lines:
            #print(line)
            line_split = line.split("  ")[0]
            replace_word = replace_map.get(idx, "")
            line_new = line_split + "  " + "".join(replace_word)
            srt_lines_new.append(line_new)
            idx += 1
    with open(srt_content_file_new, "w", encoding="utf-8") as f:    
        for line in srt_lines_new:
            f.write(line + "\n")

if __name__ == "__main__":
    content_file = sys.argv[1]
    srt_file = sys.argv[2]
    srt_file_new = sys.argv[3]

    content_map_list = gen_content_map(content_file)
    srt_map_list     = srt_to_content(srt_file)
    #for item in content_map_list: print(item)
    final_map_list    = srt_content_align(srt_map_list, content_map_list)
    map_res          = srt_content_map(final_map_list)
    for item in map_res: print(item, map_res[item])
    srt_replace(srt_file, map_res, srt_file_new)
