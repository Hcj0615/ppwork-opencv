import os
import subprocess
import time
import zipfile
from datetime import datetime
from pathlib import Path

import win32con
import win32gui

import config_collect as cg

import keyboard
import pyautogui

from pp_collect import PPCollect


def unzip_all_zips(root_dir, overwrite=False):
    """
    解压所有 ZIP 文件并统计解压后的 .txt 文件数量
    :param root_dir: 要搜索的根目录
    :param overwrite: 是否覆盖已存在的解压文件
    :return: (解压的ZIP数量, 找到的TXT文件总数)
    """
    zip_count = 0
    total_txt_files = 0
    excel_file = ''
    result_list = []

    for zip_path in Path(root_dir).rglob("*.zip"):
        try:
            # 创建解压目标目录：原目录/_unzipped/原文件名/
            excel_file = get_execl(zip_path.parent)
            unzip_dir = zip_path.parent / "_unzipped" / zip_path.stem
            unzip_dir.mkdir(parents=True, exist_ok=True)

            # 统计解压前的 .txt 文件数（避免重复统计）
            initial_txt = len(list(unzip_dir.rglob("*.txt")))

            # 解压操作
            with zipfile.ZipFile(zip_path, 'r') as zf:
                if overwrite:
                    zf.extractall(unzip_dir)
                else:
                    # 仅解压不存在的文件
                    for file in zf.namelist():
                        target = unzip_dir / file
                        if not target.exists():
                            zf.extract(file, unzip_dir)

            # 统计新增的 .txt 文件
            new_txt = len(list(unzip_dir.rglob("*.txt"))) - initial_txt
            total_txt_files += new_txt
            result_list.append([excel_file, unzip_dir])
            print(f"解压成功: {zip_path} → {unzip_dir} (+{new_txt} .txt)")
            zip_count += 1

        except zipfile.BadZipFile:
            print(f"警告: ZIP文件损坏（跳过）: {zip_path}")
        except PermissionError:
            print(f"错误: 无权限访问: {zip_path}")
        except Exception as e:
            print(f"解压失败 [{type(e).__name__}]: {zip_path} - {str(e)}")

    return zip_count, total_txt_files, result_list

def get_execl(pull_data_path):
    test = PPCollect()
    files = test.get_files_sorted_by_mtime(pull_data_path)
    for file in files:
        if '.xlsx' in file:
            print(file)
            return file


def start_task():
    PP_path = os.path.join(os.getcwd(), cg.progress_PP)

    # os.startfile(PP_path)
    process = subprocess.Popen(PP_path)

    # 等待窗口出现
    time.sleep(3)

    window_title = cg.PP_title  # 替换为实际标题（如"计算器"）
    hwnd = win32gui.FindWindow(None, window_title)

    # 4. 置顶窗口
    if hwnd:
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        win32gui.SetForegroundWindow(hwnd)  # 激活窗口
    else:
        print("未找到目标窗口！")


def upload_files(target_dir):
    test = PPCollect()
    start_task()
    zips, txts, result_list = unzip_all_zips(target_dir)

    buttons = ['files_upload.png', 'pull_task_login_id.png']
    for button in buttons:
        res, location = test.check_point(button)
        if location:
            x, y = location
            test.mouse_click(x=x, y=y)
            time.sleep(1)
            if button == 'pull_task_login_id.png':
                keyboard.write(cg.pp_login_id)

    for files in result_list:
        try:
            excel_file = os.path.join(os.getcwd(), files[0])
        except:
            print('文件出错，缺少excel文件：', files)
            continue
        zip_txt = os.path.join(os.getcwd(), files[1])
        print(zip_txt)
        buttons = ['original_file_2.png', 'result_file_2.png', 'pp_start.png']
        for button in buttons:
            res, location = test.check_point(button)
            if location:
                x, y = location
                match button:
                    case 'original_file_2.png':
                        test.mouse_click(x=x+100, y=y)
                        time.sleep(1)
                        pyautogui.hotkey('ctrl', 'a')
                        time.sleep(0.5)
                        keyboard.write(excel_file)
                    case 'result_file_2.png':
                        test.mouse_click(x=x+100, y=y)
                        time.sleep(1)
                        pyautogui.hotkey('ctrl', 'a')
                        time.sleep(0.5)
                        keyboard.write(zip_txt)
                    case 'pp_start.png':
                        test.mouse_click(x, y)
                        time.sleep(1)
        for x in range(10):
            image = 'upload_over.png'
            res, location = test.check_point(image)
            time.sleep(10)
            if location:
                break
        file_path = os.path.join(os.getcwd(), 'not_upload.txt')
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(zip_txt + '\n')
            f.close()
    print("\n=== 解压统计 ===")
    print(f"解压 ZIP 文件数量: {zips}")
    print(f"发现的 .txt 文件总数: {txts}")
    print(result_list)


def remove_empty_folders(target_dir):
    """递归删除所有空文件夹"""
    path = os.path.join(os.getcwd(), target_dir)
    for root, dirs, files in os.walk(path, topdown=False):
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            try:
                if not os.listdir(folder_path):  # 如果文件夹为空
                    os.rmdir(folder_path)  # 删除空文件夹
                    print(f"已删除空文件夹: {folder_path}")
            except (PermissionError, OSError) as e:
                print(f"无法删除 {folder_path}: {e}")


# 使用示例
if __name__ == "__main__":
    target_dir = "./pull_data/郑元源/2025-08-03/2025-08-03"  # 当前目录，可以修改为其他路径
    # zips, txts, result_list = unzip_all_zips(target_dir)
    #
    # print("\n=== 解压统计 ===")
    # print(f"扫描目录: {Path(target_dir).absolute()}")
    # print(f"解压 ZIP 文件数量: {zips}")
    # print(f"发现的 .txt 文件总数: {txts}")
    # print(result_list)
    # upload_files(target_dir)
    remove_empty_folders(target_dir)
