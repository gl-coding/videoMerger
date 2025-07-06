#!/usr/bin/env python3
import argparse
import re

def remove_ending_numbers(input_file, output_file):
    """
    从文本文件中读取内容，去除每行末尾的数字，并写入新文件
    如果行尾没有标点符号，则添加句号
    跳过空行
    
    Args:
        input_file (str): 输入文件路径
        output_file (str): 输出文件路径
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f_in:
            lines = f_in.readlines()
        
        # 处理每一行，去除末尾数字
        processed_lines = []
        for line in lines:
            # 去除行首尾空白字符
            line = line.strip()
            
            # 跳过空行
            if not line:
                processed_lines.append('\n')
                continue
            
            # 保存原始的末尾标点符号
            original_punctuation = ""
            punctuation_match = re.search(r'[。\.\!\?！？，,；;：:]$', line)
            if punctuation_match:
                original_punctuation = punctuation_match.group(0)
                # 先去除末尾的标点符号
                line = re.sub(r'[。\.\!\?！？，,；;：:]$', '', line)
            
            # 如果末尾是数字，则去除数字
            if re.search(r'\d+$', line):
                line = re.sub(r'\d+$', '', line)
            
            # 检查行尾是否有标点符号
            has_ending_punctuation = re.search(r'[。\.\!\?！？，,；;：:]$', line)
            
            # 如果没有标点符号，且原来有标点符号，则还原原来的标点符号
            if not has_ending_punctuation:
                if original_punctuation:
                    line += original_punctuation
                else:
                    # 如果原来也没有标点符号，则添加句号
                    line += "。"
                
            # 添加换行符
            processed_lines.append(line + '\n')
        
        # 写入处理后的内容到输出文件
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.writelines(processed_lines)
            
        print(f"处理完成！\n输入文件：{input_file}\n输出文件：{output_file}")
        
    except FileNotFoundError:
        print(f"错误：找不到输入文件 {input_file}")
    except Exception as e:
        print(f"处理过程中发生错误：{str(e)}")

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='去除文本文件中句子末尾的数字并确保每行有标点符号')
    parser.add_argument('input_file', help='输入文件路径')
    parser.add_argument('output_file', help='输出文件路径')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 处理文件
    remove_ending_numbers(args.input_file, args.output_file)

if __name__ == '__main__':
    main() 