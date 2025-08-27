import os.path

import requests


def download_image(url, save_path):
        try:
            # 发送 HTTP GET 请求
            response = requests.get(url, verify=False, stream=True)
            response.raise_for_status()  # 检查请求是否成功

            # 以二进制写入模式打开文件
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"图片已成功下载到: {save_path}")
            return True
        except Exception as e:
            print(f"下载图片时出错: {e}")
            return False

def save_image(url):
    save_path = r'F:\项目代码工程\pythonProject\games_execute_Zombie\pythonProject1\collect\image'
    file_name = os.path.join(save_path, 'image1.png')
    result = download_image(url, save_path)
    if not result:
        return
    print(file_name)
    return file_name


if __name__ == '__main__':
    url = 'https://img.pddpic.com/mms-material-img/2023-03-08/b8a0c12e-c210-416b-b8c2-0a5ab337670c.jpeg'
    # save_path = 'F:\项目代码工程\pythonProject\games_execute_Zombie\pythonProject1\collect\新版采集\mms-material-img.png'
    # download_image(url, save_path)
    save_image(url)
