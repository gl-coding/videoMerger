import requests

url_base = 'http://39.105.213.3'
#url_base = 'http://127.0.0.1:8000'

file_path = 'db.sqlite3'
description = 'default'

def upload_file(file_path, description):
    url = url_base + '/api/upload/'
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'description': description,
            'folder': 1  # 文件夹ID
        }
        response = requests.post(url, files=files, data=data)
        print(response.json())

def clear_folder(folder_id):
    url = url_base + '/api/folders/clear/' + str(folder_id) + '/'
    response = requests.post(url)
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
    #upload_file(file_path, description)
    clear_folder(4)
    #download_audio_files(4)

