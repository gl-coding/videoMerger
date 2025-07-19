import os
import sys
import pypinyin
from difflib import SequenceMatcher

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
def srt_content_align_old(srt_map_list, content_map_list):
    final_map_list = []
    cnt = 0
    print(len(srt_map_list), len(content_map_list))
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

#对其srt文件
def srt_content_align(srt_map_list, content_map_list, debug=True):
    final_map_list = []
    cnt = 0
    print(len(srt_map_list), len(content_map_list))
    for i in range(len(content_map_list)):
        if i >= len(content_map_list):
            break
        print("content_map_list[i]:", content_map_list[i])
        word   = content_map_list[i][0]
        pinyin = content_map_list[i][1]
        word_punc = content_map_list[i][2]
        if cnt < len(srt_map_list):
            map_word = srt_map_list[cnt]
            idx_srt = map_word[0]
            word_srt = map_word[1]
            pinyin_srt = map_word[2]
            content_pre_line = "".join([item[0] for item in content_map_list[:i+1]])
            srt_pre_line = "".join([item[1] for item in srt_map_list[:cnt+1]])
            sim = similarity_get(content_pre_line, srt_pre_line)
            sim_pinyin = similarity_pinyin_get(content_pre_line, srt_pre_line)
            if debug:
                print("++++++++++++++++++++++++++++")
                print(content_pre_line)
                print(srt_pre_line)
                print("sim:", sim, "sim_pinyin:", sim_pinyin)
            if  sim_pinyin > 0.999 and sim < 1.0:
                if debug: print("=======================sim_pinyin > 0.999 and sim < 1.0==================================")
                srt_map_list[cnt] = [idx_srt, word, pinyin]
                item = [idx_srt, word, pinyin, word, pinyin, word_punc]
                if debug:
                    content_pre_line = "".join([item[0] for item in content_map_list[:i+1]])
                    srt_pre_line = "".join([item[1] for item in srt_map_list[:cnt+1]])
                    sim = similarity_get(content_pre_line, srt_pre_line)
                    sim_pinyin = similarity_pinyin_get(content_pre_line, srt_pre_line)
                    print(content_pre_line)
                    print(srt_pre_line)
                    print("微调后 sim:", sim, "sim_pinyin:", sim_pinyin)
                final_map_list.append(item)
                cnt += 1
            elif not (sim > 0.999 or sim_pinyin > 0.999):
                if i+1 >= len(content_map_list) or cnt+1 >= len(srt_map_list):
                    print("=======================sim < 1, 进入纠错模式, 但是没有下一个字了==================================")
                    item = [idx_srt, word, pinyin, word, pinyin, word_punc]
                    final_map_list.append(item)
                    print(item)
                    cnt += 1
                    continue
                content_next_word = content_map_list[i+1][0]
                content_next_pinyin = content_map_list[i+1][1]
                srt_next_word = srt_map_list[cnt+1][1]
                srt_next_pinyin = srt_map_list[cnt+1][2]
                last_sim = similarity_get(content_next_pinyin, pinyin_srt)
                if debug: 
                    print("=======================sim < 1, 进入纠错模式==================================")
                    print(content_next_word, content_next_pinyin)
                    print(srt_next_word, srt_next_pinyin)
                    print("纠错前last_sim:", last_sim, content_next_pinyin, pinyin_srt)
                if last_sim > 0.9:
                    if debug: print("=======================纠错成功==================================")
                    srt_map_list.insert(cnt, [idx_srt, word, pinyin])
                    if debug: print(srt_map_list[cnt])
                    content_pre_line = "".join([item[0] for item in content_map_list[:i+1]])
                    srt_pre_line = "".join([item[1] for item in srt_map_list[:cnt+1]])
                    sim = similarity_get(content_pre_line, srt_pre_line)
                    item = [idx_srt, word, pinyin, word, pinyin, word_punc]
                    final_map_list.append(item)
                    if debug: 
                        print("---------------------------")
                        print(content_pre_line)
                        print(srt_pre_line)
                        print("纠错后sim:", sim)
                    cnt += 1
                    continue
                else:
                    window_size = 5
                    content_next_words = content_map_list[i:min(i+window_size, len(content_map_list))]
                    srt_next_words = srt_map_list[cnt:min(cnt+window_size, len(srt_map_list))]
                    print(content_next_words)
                    print(srt_next_words)
                    content_prefix, srt_prefix = get_max_match_prefix(content_next_words, srt_next_words)
                    content_prefix_len = len(content_prefix)
                    srt_prefix_len = len(srt_prefix)
                    if content_prefix_len != 0 and srt_prefix_len != 0:
                        content_prefix_merge = mege_content_seg(content_prefix)
                        srt_prefix_merge = mege_srt_seg(srt_prefix)
                        print("--------------------------------")
                        print("content_prefix_len != 0 and srt_prefix_len != 0")
                        print(content_prefix)
                        print(srt_prefix)
                        print("------------init_prefix_merge--------------------")
                        print(content_prefix_merge)
                        print(srt_prefix_merge)
                        srt_prefix_merge[0][1] = content_prefix_merge[0][0]
                        srt_prefix_merge[0][2] = content_prefix_merge[0][1]
                        print("------------replace_prefix_merge--------------------")
                        print(content_prefix_merge)
                        print(srt_prefix_merge)
                        content_map_list = content_map_list[:i] + content_prefix_merge + content_map_list[i+len(content_prefix):]
                        srt_map_list = srt_map_list[:cnt] + srt_prefix_merge + srt_map_list[cnt+len(srt_prefix):]
                        print(content_map_list)
                        print(srt_map_list)
                        item = [srt_prefix_merge[0][0], srt_prefix_merge[0][1], srt_prefix_merge[0][2], content_prefix_merge[0][0], content_prefix_merge[0][1], content_prefix_merge[0][2]]
                        print("||||||||||||||||||||||||||||||||||||||")
                        print(item)
                        final_map_list.append(item)
                        cnt += 1
                    else:
                        continue
            else:
                item = [idx_srt, word_srt, pinyin_srt, word, pinyin, word_punc]
                final_map_list.append(item)
                print(item)
                cnt += 1
        # else:
        #     item = [idx, word, pinyin, ["None"], ["None"], ["None"]]  
        #     final_map_list.append(item)
        #     print(item)
        #     cnt += 1
    #similarity_check(final_map_list)
    return final_map_list

def mege_content_seg(content_seg):
    res = ["", [], ""]
    for item in content_seg:
        res[0] += item[0]
        res[1] += item[1]
        res[2] += item[2]
    return [res]

def mege_srt_seg(srt_seg):
    res = [0, "", []]
    for item in srt_seg:
        res[0] = item[0]
        res[1] += item[1]
        res[2] += item[2]
    return [res]

def get_max_match_prefix(content_segs, srt_segs):
    def get_sim_cnt(content_seg, srt_seg):
        cnt = 0
        min_idx = -1
        for i in range(min(len(content_seg), len(srt_seg))):
            if not content_seg[i] or not srt_seg[i]:
                continue
            elif content_seg[i][2] == srt_seg[i][1]:
                if min_idx == -1:
                    min_idx = i
                cnt += 1
        return cnt, min_idx
    
    new_content_words = [None] * len(srt_segs) + content_segs
    sim_cnt_max = 0
    content_seg_max = []
    srt_seg_max = []
    min_idx_max = -1
    for i in range(len(new_content_words)):
        seg_content_words = new_content_words[i:min(i+len(srt_segs), len(new_content_words))]
        seg_content_len = len(seg_content_words)
        seg_srt_words = srt_segs[:min(seg_content_len, len(srt_segs))]
        sim_cnt, min_idx = get_sim_cnt(seg_content_words, seg_srt_words)
        if sim_cnt > sim_cnt_max:
            sim_cnt_max = sim_cnt
            content_seg_max = seg_content_words
            srt_seg_max = seg_srt_words
            min_idx_max = min_idx
            seg_content_min_idx = i + min_idx
            seg_srt_min_idx = min_idx
        print("--------------------------------")
        print(seg_content_words)
        print(seg_srt_words)
        print(sim_cnt)
        print(min_idx)
    print("************************************************")
    print(content_seg_max)
    print(srt_seg_max)
    print(sim_cnt_max)
    print(min_idx_max)
    print(seg_content_min_idx)
    print(seg_srt_min_idx)
    content_prefix = [item for item in new_content_words[:seg_content_min_idx] if item]
    srt_prefix = [item for item in srt_segs[:seg_srt_min_idx] if item]
    content_prefix_merge = mege_content_seg(content_prefix)
    print(content_prefix)
    print(srt_prefix)
    print(content_prefix_merge)
    return content_prefix, srt_prefix

def similarity_pinyin_get(content_pre_line, srt_pre_line):
    # 计算content_pre_line和srt_pre_line的相似度
    cnt = 0
    for i in range(len(content_pre_line)):
        content_pinyin = "".join(pypinyin.lazy_pinyin(content_pre_line[i]))
        srt_pinyin = "".join(pypinyin.lazy_pinyin(srt_pre_line[i]))
        #计算两个拼音的相似度
        seq = SequenceMatcher(None, content_pinyin, srt_pinyin)
        if seq.ratio() > 0.5:
            cnt += 1
    return cnt/len(content_pre_line)

def similarity_get(content_pre_line, srt_pre_line):
    # 计算content_pre_line和srt_pre_line的相似度
    cnt = 0
    for i in range(len(content_pre_line)):
        if content_pre_line[i] == srt_pre_line[i]:
            cnt += 1
    return cnt/len(content_pre_line)

def similarity_check(final_map_list):
    item_list = [it for item in final_map_list for it in item[2]]
    item_list_txt = [it for item in final_map_list for it in item[4]]
    print(len(item_list), len(item_list_txt))
    #print(item_list)
    #print(item_list_txt)

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
    final_map_list    = srt_content_align(srt_map_list, content_map_list, debug=True)
    #exit(0)
    for item in final_map_list:
        print(item)
    #exit(0)
    map_res          = srt_content_map(final_map_list)
    #for item in map_res: print(item, map_res[item])
    srt_replace(srt_file, map_res, srt_file_new)
