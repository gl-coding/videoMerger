import requests
import sys
import argparse

url_base = 'http://39.105.213.3'
#url_base = 'http://127.0.0.1:8000'

file_path = 'db.sqlite3'
description = 'default'

def upload_file(file_path, description, folder_id=1):
    url = url_base + '/api/upload/'
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'description': description,
            'folder': folder_id  # 文件夹ID
        }
        response = requests.post(url, files=files, data=data)
        print(response.json())

def clear_folder(folder_id):
    url = url_base + '/api/folders/clear/' + str(folder_id) + '/'
    response = requests.post(url)
    print(response.json())

def clear_content_data():
    url = 'https://aliyun.ideapool.club/datapost/type-content/clear/'
    response = requests.get(url)
    print(response.json())

def download_audio_files(folder_id):
    #获取指定文件夹下的所有文件
    url = url_base + '/api/folders/' + str(folder_id) + '/files/?all=true'
    response = requests.get(url)
    files = response.json()
    files_list = files.get("data", {}).get("files", [])
    for file in files_list:
        file_name = file.get("static_url", "")
        full_url = url_base + file_name
        print(full_url)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='API操作工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # upload命令
    upload_parser = subparsers.add_parser('upload', help='上传文件')
    upload_parser.add_argument('file_path', help='要上传的文件路径')
    upload_parser.add_argument('-d', '--description', default='default', help='文件描述 (默认: default)')
    upload_parser.add_argument('-f', '--folder', type=int, default=1, help='文件夹ID (默认: 1)')
    
    # clear命令
    clear_parser = subparsers.add_parser('clear', help='清空文件夹')
    clear_parser.add_argument('folder_id', type=int, help='要清空的文件夹ID')

    # clear_content命令
    clear_content_parser = subparsers.add_parser('clear_content', help='清空内容数据')
    
    # download命令
    download_parser = subparsers.add_parser('download', help='下载音频文件')
    download_parser.add_argument('folder_id', type=int, help='要下载的文件夹ID')
    
    args = parser.parse_args()
    
    if args.command == 'upload':
        upload_file(args.file_path, args.description, args.folder)
    elif args.command == 'clear':
        clear_folder(args.folder_id)
    elif args.command == 'download':
        download_audio_files(args.folder_id)
    elif args.command == 'clear_content':
        clear_content_data()
    else:
        parser.print_help()

