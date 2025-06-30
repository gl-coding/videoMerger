#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音数据提交工具
主要功能：提交语音数据到远程服务器
支持功能：数据提交、列表查询、数据清理
"""

import requests
import json
import argparse
import sys
import os

# 服务器地址
BASE_URL = "https://aliyun.ideapool.club/datapost"

def submit_voice_data(voice_data, outfile, content, verbose=True):
    """提交语音数据到服务器
    
    Args:
        voice_data (str): 语音数据内容或文件路径
        outfile (str): 输出文件名
        content (str): 相关的文本内容
        verbose (bool): 是否显示详细信息
    
    Returns:
        dict: 提交结果，包含status和id等信息
    """
    if verbose:
        print("=== 提交语音数据 ===")
    
    url = f"{BASE_URL}/voice/"
    
    voice_content = voice_data
    
    data = {
        "voice": voice_content,
        "outfile": outfile,
        "content": content
    }
    
    try:
        if verbose:
            print(f"提交数据到: {url}")
            print(f"输出文件: {outfile}")
            print(f"内容长度: {len(content)} 字符")
        
        response = requests.post(url, json=data)
        result = response.json()
        
        if verbose:
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get('status') == 'success':
            if verbose:
                print("✅ 数据提交成功")
            return {
                'success': True,
                'id': result.get('id'),
                'message': result.get('message', '提交成功')
            }
        else:
            if verbose:
                print("❌ 数据提交失败")
            return {
                'success': False,
                'error': result.get('message', '提交失败'),
                'status_code': response.status_code
            }
            
    except Exception as e:
        if verbose:
            print(f"❌ 提交异常: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_voice_list(verbose=True):
    """获取语音数据列表
    
    Args:
        verbose (bool): 是否显示详细信息
    
    Returns:
        dict: 查询结果
    """
    if verbose:
        print("=== 获取数据列表 ===")
    
    url = f"{BASE_URL}/voice/list/"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        if verbose:
            print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get('status') == 'success':
            if verbose:
                print("✅ 获取列表成功")
                print(f"总数据量: {result.get('total_count', 0)}")
            return {
                'success': True,
                'data': result.get('data', []),
                'total_count': result.get('total_count', 0)
            }
        else:
            if verbose:
                print("❌ 获取列表失败")
            return {
                'success': False,
                'error': result.get('message', '获取失败'),
                'status_code': response.status_code
            }
            
    except Exception as e:
        if verbose:
            print(f"❌ 获取列表异常: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def clear_voice_data(verbose=True):
    """清空所有语音数据
    
    Args:
        verbose (bool): 是否显示详细信息
    
    Returns:
        dict: 清理结果
    """
    if verbose:
        print("=== 清空数据 ===")
    
    url = f"{BASE_URL}/voice/clear/"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        if verbose:
            print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get('status') == 'success':
            if verbose:
                print("✅ 数据清空成功")
            return {
                'success': True,
                'message': result.get('message', '清空成功')
            }
        else:
            if verbose:
                print("❌ 数据清空失败")
            return {
                'success': False,
                'error': result.get('message', '清空失败'),
                'status_code': response.status_code
            }
            
    except Exception as e:
        if verbose:
            print(f"❌ 清空数据异常: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """主函数 - 解析命令行参数并执行相应功能"""
    parser = argparse.ArgumentParser(
        description='语音数据提交工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 直接输入文本内容（需要-c参数）
  python clone_voice.py -v "语音内容" -o "output.txt" -c "文本内容"
  
  # 从文本文件读取内容（voice和content都使用文件内容）
  python clone_voice.py -f "content.txt" -o "result.txt"
  
  # 自定义content字段（voice使用文件内容，content使用自定义内容）
  python clone_voice.py -f "content.txt" -o "result.txt" -c "自定义描述"
  
  # 支持任何文本文件格式
  python clone_voice.py -f "script.srt" -o "output.txt"
  python clone_voice.py -f "document.md" -o "result.txt"
  python clone_voice.py -f "data.json" -o "output.txt"
  
  # 查看数据列表
  python clone_voice.py --list
  
  # 清空所有数据
  python clone_voice.py --clear
  
  # 静默模式提交
  python clone_voice.py -v "内容" -o "out.txt" -c "文本" --quiet
        """
    )
    
    # 主要功能参数
    parser.add_argument('-v', '--voice', help='语音数据内容（直接输入文本）')
    parser.add_argument('-f', '--file', help='文本文件路径（读取文件内容作为语音数据）')
    parser.add_argument('-o', '--output', help='输出文件名')
    parser.add_argument('-c', '--content', help='相关文本内容（使用-f参数时可选，默认使用文件内容）')
    
    # 功能控制参数
    parser.add_argument('--list', action='store_true', help='显示数据列表')
    parser.add_argument('--clear', action='store_true', help='清空所有数据')
    
    # 输出控制参数
    parser.add_argument('--quiet', action='store_true', help='静默模式，减少输出信息')
    parser.add_argument('--json', action='store_true', help='以JSON格式输出结果')
    
    args = parser.parse_args()
    
    # 设置详细输出模式
    verbose = not args.quiet
    
    # 如果没有任何参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # 处理查看列表功能
    if args.list:
        result = get_voice_list(verbose)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 处理清空数据功能
    if args.clear:
        result = clear_voice_data(verbose)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 处理数据提交功能（主要功能）
    voice_data = None
    file_content = None
    
    # 读取文件内容（如果提供了-f参数）
    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ 文件不存在: {args.file}")
            return
        
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                file_content = f.read().strip()
            if verbose:
                print(f"从文件读取内容: {args.file}")
                print(f"文件内容长度: {len(file_content)} 字符")
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return
    
    # 确定voice字段的值
    if args.voice:
        voice_data = args.voice
        if verbose:
            print(f"voice字段使用-v参数值，长度: {len(voice_data)} 字符")
    elif file_content:
        voice_data = file_content
        if verbose:
            print(f"voice字段使用文件内容，长度: {len(voice_data)} 字符")
            print(f"内容预览: {voice_data[:100]}{'...' if len(voice_data) > 100 else ''}")
    else:
        print("❌ 请指定语音数据 (-v) 或文本文件 (-f)")
        print("   支持格式:")
        print("   • 直接文本: -v \"直接输入文本\" -c \"描述\" (需要-c参数)")
        print("   • 文本文件: -f \"content.txt\" (voice和content都使用文件内容)")
        parser.print_help()
        return
    
    if not args.output:
        print("❌ 请指定输出文件名 (-o)")
        parser.print_help()
        return
    
    # 当使用-f参数时，-c参数可选
    if not args.content and not args.file:
        print("❌ 请指定文本内容 (-c)")
        parser.print_help()
        return
    
    # 确定content字段的值
    if args.content:
        content = args.content
        if verbose:
            print(f"content字段使用-c参数值，长度: {len(content)} 字符")
    elif file_content:
        # 使用从文件读取的内容作为content
        content = file_content
        if verbose:
            print(f"content字段使用文件内容，长度: {len(content)} 字符")
    else:
        content = ""
    
    # 提交数据
    result = submit_voice_data(voice_data, args.output, content, verbose)
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not verbose:
        # 静默模式下只显示关键信息
        if result['success']:
            print(f"提交成功，ID: {result.get('id', 'N/A')}")
        else:
            print(f"提交失败: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    main()