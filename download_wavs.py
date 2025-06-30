import requests
import os
from urllib.parse import urlparse
import time
import argparse
import json

url_base = 'http://39.105.213.3'
#url_base = 'http://127.0.0.1:8000'

def download_file(url, local_path):
    """下载单个文件到本地"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"✓ 下载成功: {local_path}")
        return True
    except Exception as e:
        print(f"✗ 下载失败: {url} - {str(e)}")
        return False

def get_filename_from_url(url):
    """从URL中提取文件名"""
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename:
        # 如果无法从URL提取文件名，使用时间戳
        timestamp = int(time.time())
        filename = f"audio_{timestamp}.wav"
    return filename

def download_audio_files(folder_id, download_dir="downloads", delete_after_download=False):
    """获取指定文件夹下的所有文件并下载到本地"""
    print(f"开始下载文件夹 {folder_id} 中的音频文件...")
    
    # 获取文件列表
    url = url_base + '/api/folders/' + str(folder_id) + '/files/?all=true'
    try:
        response = requests.get(url)
        response.raise_for_status()
        files = response.json()
        files_list = files.get("data", {}).get("files", [])
        
        if not files_list:
            print("未找到任何文件")
            return
        
        print(f"找到 {len(files_list)} 个文件")
        
        # 创建下载目录
        download_path = download_dir
        os.makedirs(download_path, exist_ok=True)
        
        success_count = 0
        delete_count = 0
        total_count = len(files_list)
        
        # 下载每个文件
        for i, file in enumerate(files_list, 1):
            file_id = file.get("id", "")
            file_name = file.get("static_url", "")
            original_name = file.get("original_name", "")
            
            if not file_name:
                print(f"跳过无效文件: {file}")
                continue
                
            full_url = url_base + file_name
            
            # 提取文件名，优先使用原始文件名
            if original_name:
                local_filename = original_name
            else:
                local_filename = get_filename_from_url(file_name)
            
            local_path = os.path.join(download_path, local_filename)
            
            print(f"[{i}/{total_count}] 下载: {original_name or local_filename}")
            
            if download_file(full_url, local_path):
                success_count += 1
                
                # 如果下载成功且需要删除，则删除服务器上的文件
                if delete_after_download and file_id:
                    if delete_file_by_id(file_id):
                        delete_count += 1
            
            # 添加小延迟避免过于频繁的请求
            time.sleep(0.1)
        
        print(f"\n下载完成! 成功: {success_count}/{total_count}")
        if delete_after_download:
            print(f"删除完成! 成功: {delete_count}/{success_count}")
        print(f"文件保存在: {os.path.abspath(download_path)}")
        
    except Exception as e:
        print(f"获取文件列表失败: {str(e)}")

def delete_all_files_in_folder(folder_id):
    """删除文件夹中的所有文件"""
    print(f"开始删除文件夹 {folder_id} 中的所有文件...")
    
    # 获取文件列表
    url = url_base + '/api/folders/' + str(folder_id) + '/files/?all=true'
    try:
        response = requests.get(url)
        response.raise_for_status()
        files = response.json()
        files_list = files.get("data", {}).get("files", [])
        
        if not files_list:
            print("未找到任何文件")
            return
        
        print(f"找到 {len(files_list)} 个文件")
        
        delete_count = 0
        total_count = len(files_list)
        
        # 删除每个文件
        for i, file in enumerate(files_list, 1):
            file_id = file.get("id", "")
            original_name = file.get("original_name", "")
            
            if not file_id:
                print(f"跳过无效文件ID: {file}")
                continue
            
            print(f"[{i}/{total_count}] 删除: {original_name}")
            
            if delete_file_by_id(file_id):
                delete_count += 1
            
            # 添加小延迟避免过于频繁的请求
            time.sleep(0.1)
        
        print(f"\n删除完成! 成功: {delete_count}/{total_count}")
        
    except Exception as e:
        print(f"获取文件列表失败: {str(e)}")

def delete_file_by_id(file_id, method='POST'):
    """删除指定ID的文件"""
    url = f'{url_base}/api/files/delete/{file_id}/'
    
    if method.upper() == 'DELETE':
        response = requests.delete(url)
    else:
        response = requests.post(url)
    
    print(f"\n🗑️  尝试删除文件ID {file_id} (使用 {method} 方法)")
    print(f"响应状态码: {response.status_code}")
    
    try:
        data = response.json()
        if data['success']:
            print(f"✅ {data['message']}")
            print(f"   删除的文件: {data['data']['original_name']}")
            print(f"   所属文件夹: {data['data']['folder']}")
            print(f"   物理文件删除: {'是' if data['data']['physical_file_deleted'] else '否'}")
            return True
        else:
            print(f"❌ 删除失败: {data['error']}")
            return False
    except json.JSONDecodeError:
        print(f"❌ 响应解析失败: {response.text}")
        return False

def list_folder_files(folder_id):
    """仅列出文件夹中的文件，不下载"""
    url = url_base + '/api/folders/' + str(folder_id) + '/files/?all=true'
    try:
        response = requests.get(url)
        response.raise_for_status()
        files = response.json()
        files_list = files.get("data", {}).get("files", [])
        
        print(f"文件夹 {folder_id} 中的文件:")
        for i, file in enumerate(files_list, 1):
            file_id = file.get("id", "")
            file_name = file.get("static_url", "")
            original_name = file.get("original_name", "")
            full_url = url_base + file_name
            print(f"{i}. ID: {file_id} | 原名: {original_name} | URL: {full_url}")
            
    except Exception as e:
        print(f"获取文件列表失败: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='下载指定文件夹中的音频文件')
    parser.add_argument('folder_id', type=int, help='文件夹ID')
    parser.add_argument('-d', '--download-dir', default='downloads', 
                       help='下载目录 (默认: downloads)')
    parser.add_argument('-l', '--list-only', action='store_true',
                       help='仅列出文件，不下载')
    parser.add_argument('--delete-after-download', action='store_true',
                       help='下载后删除服务器上的文件')
    parser.add_argument('--delete-only', action='store_true',
                       help='仅删除文件夹中的所有文件，不下载')
    parser.add_argument('--delete-file-id', type=int,
                       help='删除指定ID的单个文件')
    
    args = parser.parse_args()
    
    try:
        if args.delete_file_id:
            # 删除指定ID的文件
            delete_file_by_id(args.delete_file_id)
        elif args.delete_only:
            # 仅删除文件夹中的所有文件
            delete_all_files_in_folder(args.folder_id)
        elif args.list_only:
            # 仅列出文件
            list_folder_files(args.folder_id)
        else:
            # 下载文件
            download_audio_files(args.folder_id, args.download_dir, args.delete_after_download)
            
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"程序执行出错: {str(e)}")

if __name__ == '__main__':
    main() 