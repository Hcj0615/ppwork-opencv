import ctypes
import sys

from log import log
import os
import traceback
from datetime import datetime

import keyboard
import subprocess
import pandas as pd

import cv2
import numpy as np
import pyautogui
import time

import win32con
import win32gui
from win32ctypes.pywin32 import pywintypes

import config_collect as cg

from get_image import download_image


class PPCollect:
    def __init__(self):
        self.file = None
        self.MOUSEEVENTF_WHEEL = 0x0800

        # 定义Windows API常量
        self.MOUSEEVENTF_LEFTDOWN = 0x0002
        self.MOUSEEVENTF_LEFTUP = 0x0004
        self.MOUSEEVENTF_RIGHTDOWN = 0x0008
        self.MOUSEEVENTF_RIGHTUP = 0x0010
        self.MOUSEEVENTF_MIDDLEDOWN = 0x0020
        self.MOUSEEVENTF_MIDDLEUP = 0x0040

        self.delete_all_files()
        self.pull_data_path = None
        self.is_collect = True
        self.count = 0
        self.collect_count = 0
        
    def setup_collect(self):
        self.count = 0
        self.collect_count = 0
        today = datetime.today().date()
        timestamp = int(time.time())
        self.pull_data_path = os.path.join(os.getcwd(), 'pull_data', str(today), str(timestamp))
        os.makedirs(self.pull_data_path, exist_ok=True)
        log.info('*'*10 + f'{self.pull_data_path}开始' + '*'*10)
        self.check_input()
        self.refresh_goods()
        self.mouse_click(cg.x, cg.y)
        self.kill_task()
        self.start_task()
        pyautogui.click(cg.x, cg.y)
        self.get_pull_data()

    def teardown_collect(self):
        self.check_input()
        self.out_data()
        self.close_agent()
        self.upload_collect_file()
        self.kill_task()

    def get_pull_data(self):
        """撞库，获取数据"""
        self.mouse_click(x=cg.x, y=cg.y)
        for j in range(cg.get_pull_counts):
            pyautogui.press('down', presses=30)
            try:
                df = self.get_data_from_excel()
                print(df)
                break
            except:
                time.sleep(2)
                continue
        self.mouse_scroll(20)

    def kill_task(self):
        tasks = [cg.progress_PP, cg.progress_shops]
        button = 'stop_collect.png'
        self.find_and_click(button)
        for task in tasks:
            os.system(f'taskkill /IM {task} /F')

    def start_task(self):
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

        buttons_pp = ['pp_pull_task.png', 'pull_task_login_id.png', 'pull_data_path.png', 'pp_start.png']
        for button in buttons_pp:
            time.sleep(1)
            res = self.find_and_click(button)
            if not res:
                log.error('启动PP_Work失败')
                raise Exception('启动PP_Work失败')
            match button:
                case 'pull_task_login_id.png':
                    time.sleep(1)
                    keyboard.write(cg.pp_login_id, delay=0.01)
                case 'pull_data_path.png':
                    time.sleep(1)
                    keyboard.write(self.pull_data_path, delay=0.01)
                    pyautogui.press('enter')

        time.sleep(1)
        image = 'pp_work.png'
        res, location = self.check_point(image)
        if location:
            x, y = location
            x2 = 1390
            y2 = 55
            pyautogui.moveTo(x, y)
            # 按下鼠标左键
            pyautogui.mouseDown()
            # 拖动文件到目标位置，耗时 1 秒
            pyautogui.moveTo(x2, y2, duration=1)
            # 释放鼠标左键
            pyautogui.mouseUp()

        time.sleep(2)

        # os.startfile(shops_path)
        process = subprocess.Popen(cg.shops_path)  # 示例：记事本

        # 等待窗口出现
        time.sleep(3)

        window_title = cg.collect_title  # 替换为实际标题（如"计算器"）
        hwnd = win32gui.FindWindow(None, window_title)

        # 4. 置顶窗口
        if hwnd:
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            win32gui.SetForegroundWindow(hwnd)  # 激活窗口
        else:
            print("未找到目标窗口！")

        buttons_shops = ['shops_login.png', 'goods_collect.png', ]
        for button in buttons_shops:
            time.sleep(3)
            res = self.find_and_click(button)
            if not res:
                log.error('启动多多采宝失败')
                raise Exception('启动多多采宝失败')

        time.sleep(1)
        button = 'shops_bar.png'
        res, location = self.check_point(button)
        x, y = location
        x2, y2 = 260, 425
        pyautogui.moveTo(x, y)
        # 按下鼠标左键
        pyautogui.mouseDown()
        # 拖动文件到目标位置，耗时 1 秒
        pyautogui.moveTo(x2, y2, duration=1)
        # 释放鼠标左键
        pyautogui.mouseUp()

    def check_point(self, point, confidence=0.6, t: float = 0.5, times=2):
        """寻找检测点，并返回坐标"""
        template_path = "data/%s" % point
        print(f"开始寻找监测点{point}，预计耗时{t * times}s")
        for i in range(times):
            time.sleep(t)
            location = self.find_image_on_screen(template_path, confidence=confidence)
            if location:
                print(f"找到监测点{point}")
                return True, location
        print(f"未找到监测点{point}")
        return False, location

    def collector_find_and_click(self, image):
        """监控采集器的确认添加按钮"""
        result, location = self.check_point(image, confidence=0.8, times=2)
        if not location:
            print('没有找到按钮：', image)
            return
        x, y = location
        # pyautogui.click(x, y)
        self.mouse_click(x=x, y=y)
        time.sleep(0.5)
        self.mouse_click(x=cg.x, y=cg.y)
        self.collector_find_and_click(image)

    def find_and_click(self, image):
        """监控采集器的确认添加按钮"""
        result, location = self.check_point(image, confidence=0.8, times=2)
        if not result:
            print('没有找到按钮：', image)
            return False
        x, y = location
        # pyautogui.click(x, y)
        self.mouse_click(x=x, y=y)
        return True

    def match_screen(self, img, fx_scale, fy_scale):
        return cv2.resize(img, None, fx=fx_scale, fy=fy_scale)

    def find_image_on_screen(self, template_path, confidence=0.8):
        """
        在屏幕上查找指定的图片。
        :param template_path: 模板图片的路径
        :param confidence: 匹配置信度（0到1之间）
        :return: 如果找到图片，返回其中心坐标；否则返回None
        """
        # screenshot, rect = self.get_handle_windows_screen()
        # screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        screen_width, screen_height = pyautogui.size()
        screenshot = pyautogui.screenshot(region=(0, 0, screen_width, screen_height))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 读取模板图片
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        h, w = template.shape[:2]  # 彩色图取前2维 (h, w, _)
        # print(f"模板尺寸：宽度={w}, 高度={h}")
        # template = cv2.imread(template_path)
        if 'image' in template_path:
            scale = cg.image_height / h * cg.percent
            template = self.match_screen(template, scale, scale)
        elif 'owner_center' in template_path:
            template = self.match_screen(template, cg.percent, cg.percent)

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 使用模板匹配

        # cv2.imshow('Image', template)
        # cv2.waitKey(0)  # 等待任意按键关闭窗口
        # cv2.destroyAllWindows()

        # 如果匹配度高于置信度，则返回中心坐标
        if max_val >= confidence:
            template_height, template_width = template.shape[:2]
            center_x = max_loc[0] + template_width // 2
            center_y = max_loc[1] + template_height // 2

            return center_x, center_y
        else:
            return None

    def get_files_sorted_by_mtime(self, directory):
        # 获取目录下所有文件和子目录
        entries = [os.path.join(directory, f) for f in os.listdir(directory)]

        # 过滤出文件（排除目录）
        files = [f for f in entries if os.path.isfile(f)]

        # 按修改时间排序（最新的在前）
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        return files

    def get_data_from_excel(self):
        # file_path = os.path.join(os.getcwd(), self.pull_data_path)
        files = self.get_files_sorted_by_mtime(self.pull_data_path)

        self.file = files[0]
        return pd.read_excel(self.file, sheet_name='Sheet1')

    def get_image_list_from_dir(self):
        dir_name = os.path.join(os.getcwd(), 'image')
        files = self.get_files_sorted_by_mtime(dir_name)
        image_list = list()
        for file in files:
            image = file.split('\\')[-1]
            if 'png' in image:
                image_list.append(image)

        return image_list

    def download_image(self, image_list, url=None):
        save_path = os.path.join(os.getcwd(), 'image')
        df = self.get_data_from_excel()
        if url and df['image_url'].iloc[-1] != url:
            matching_indices = df.index[df['image_url'] == url]
            index = matching_indices[-1]
            df = df.iloc[index + 1:]
        url_list = df['image_url']
        for url in url_list:
            image_name = f'image{url[-20:]}'
            save_image = os.path.join(save_path, image_name)
            result = download_image(url, save_image)
            if result:
                image_list.append(image_name)
        return image_list, url_list.iloc[-1]

    def download_image1(self, image_list, url=None):
        save_path = os.path.join(os.getcwd(), 'image')
        df = self.get_data_from_excel()
        if df.shape[0] > cg.get_data_num:
            if self.count > 3:
                print(f'采集的数据达到{cg.get_data_num}，本次采集结束')
                log.info(f'采集的数据达到{cg.get_data_num}，本次采集结束')
                # raise Exception(f'采集的数据达到{cg.get_data_num}，本次采集结束')
            self.count += 1
        if url and df['image_url'].iloc[-1] != url:
            matching_indices = df.index[df['image_url'] == url]
            index = matching_indices[-1]
            df = df.iloc[index + 1:]
            url_list = df['image_url']
            for url in url_list:
                image_name = f'image{url[-20:]}'
                save_image = os.path.join(save_path, image_name)
                result = download_image(url, save_image)
                if result:
                    image_list.append(image_name)
            return image_list, url_list.iloc[-1]
        elif not url or url == '':
            url_list = df['image_url']
            for url in url_list:
                image_name = f'image{url[-20:]}'
                save_image = os.path.join(save_path, image_name)
                result = download_image(url, save_image)
                if result:
                    image_list.append(image_name)
            return image_list, url_list.iloc[-1]
        else:
            return image_list, url

    def get_image_list(self, image_list, url, is_get=True):
        while is_get is True:
            image_list, url = self.download_image1(image_list, url=url)
            time.sleep(3)

    def return_back_home(self):
        point = 'collect.png'
        res, location = self.check_point(point)
        if location:
            button = 'return_back.png'
            self.find_and_click(button)
            time.sleep(1)
            self.mouse_click(cg.x, cg.y)
            return
        else:
            points = ['goods_search.png', 'sell_out.png', 'pdd_login.png', 'safe_verify.png']
            for point in points:
                res, location = self.check_point(point)
                if location:
                    if point == 'sell_out.png' or point == 'pdd_login.png':
                        log.error('商品售罄，疑似被风控，程序运行结束')
                        sys.exit('商品售罄，疑似被风控，程序运行结束')
                    if point == 'safe_verify.png':
                        log.error('需要安全验证')
                        res, location = self.check_point(point)
                        while location:
                            time.sleep(10)
                            res, location = self.check_point(point)
                        time.sleep(10)
                        self.return_back_home()
                        break
                    button = 'return_back.png'
                    self.find_and_click(button)
                    time.sleep(1)
                    self.mouse_click(cg.x, cg.y)
                    return
        point = 'owner_center.png'
        res, location = self.check_point(point)
        if not location:
            print('找不到主页， 程序暂停')
            log.error('找不到主页， 程序暂停')
            while not location:
                time.sleep(10)
                res, location = self.check_point(point)
            # os.system(f'taskkill /IM chrome.exe /F')
            time.sleep(1)
            self.mouse_click(cg.x, cg.y)

    def delete_shops_dialog(self):
        button = 'delete.png'
        res = self.find_and_click(button)
        while res:
            time.sleep(0.5)
            self.find_and_click('comfirn_delete.png')
            time.sleep(0.5)
            res = self.find_and_click(button)

    def turn_on_collect(self):
        button = 'start_collector.png'
        res, location = self.check_point(button)
        x, y = location
        self.mouse_click(x=x, y=y)

    def find_multiple_matches(self, template_path, threshold=0.9):
        """匹配多个相同模板，一张图片上能找到多个目标值"""
        # # 读取模板
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        template = self.match_screen(template, cg.percent, cg.percent)
        # cv2.imshow('Image', template)
        # cv2.waitKey(0)  # 等待任意按键关闭窗口
        # cv2.destroyAllWindows()

        screen_width, screen_height = pyautogui.size()
        screenshot = pyautogui.screenshot(region=(0, 0, screen_width, screen_height))
        # 截取屏幕截图

        # screenshot = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        # 确保图像和模板类型一致
        img = img.astype(np.float32)
        template = template.astype(np.float32)

        # 执行模板匹配
        res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)

        # 找到所有高于阈值的匹配位置
        loc = np.where(res >= threshold)

        # 存储匹配结果
        matches = []
        for pt in zip(*loc[::-1]):  # 交换x,y坐标
            matches.append(pt)

        # 非极大值抑制(NMS) - 去除重叠的匹配
        matches = self.non_max_suppression(matches, template.shape)

        return matches

    def non_max_suppression(self, boxes, template_shape, overlapThresh=0.5):
        # 实现非极大值抑制
        if len(boxes) == 0:
            return []

        # 转换坐标为(x1,y1,x2,y2)格式
        boxes = np.array([(x, y, x + template_shape[1], y + template_shape[0]) for (x, y) in boxes])

        # 按置信度排序(这里简化为按y坐标排序)
        pick = []
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]

        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(y2)

        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)

            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])

            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)

            overlap = (w * h) / area[idxs[:last]]

            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0])))

        return boxes[pick][:, :2]  # 返回(x,y)坐标

    def check_input(self):
        input_name = 'input.png'
        res, location = self.check_point(input_name)
        if not location:
            self.mouse_click(location)
            time.sleep(0.5)
            self.find_and_click('wx_input.png')
            time.sleep(0.5)
            self.find_and_click('eng_input.png')

    def out_data(self, n=0):
        buttons = ['stop_collect.png', cg.button, 'out_data.png', 'out_data_type.png', 'output_data_path.png', 'save_out_data.png']
        for button in buttons:
            # self.find_and_click(button)
            rea, location = self.check_point(button, confidence=0.8)
            if not location:
                if button == buttons[-1]:
                    if n > 6:
                        raise
                    n += 1
                    self.out_data()
                continue
            pyautogui.click(location)
            if button == buttons[-2]:
                keyboard.write(self.pull_data_path, delay=0.01)
                pyautogui.press('enter')
            time.sleep(2)

    def delete_all_files(self):
        """删除文件夹内所有文件（保留子文件夹结构）"""
        folder_path = os.path.join(os.getcwd(), 'image')
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)  # 删除文件
                elif os.path.isdir(file_path):
                    # 如需删除子文件夹内的文件，取消下一行注释
                    # delete_all_files(file_path)  # 递归删除子文件夹内容
                    pass
            except Exception as e:
                print(f"删除失败 {file_path}: {e}")

    def close_agent(self):
        button = 'stop_collect.png'
        res, location = self.check_point(button)
        if location:
            pyautogui.click(location)

    def set_progress_top(self):
        handle_pp = self.get_handle(title=cg.PP_title)
        self.set_window_always_on_top(handle=handle_pp, title=cg.PP_title)
        time.sleep(1)
        handle_collect = self.get_handle(title=cg.collect_title)
        self.set_window_always_on_top(handle=handle_collect, title=cg.collect_title)

    def collect_data(self, image_list):
        self.mouse_scroll(-5)
        point = 'data\\yuan.png'
        matches = self.find_multiple_matches(point)
        while len(matches) < cg.yuan_num:
            pyautogui.press('down', presses=1)
            matches = self.find_multiple_matches(point)
        for index, image_name in enumerate(image_list):
            result = self.find_image_on_screen_windows(image_name)
            if result:
                button = cg.button
                self.collector_find_and_click(button)
                image_list.pop(index)
                self.return_back_home()
                time.sleep(2)
            else:
                print(f"队列中待采集商品{len(image_list)}个, 当前商品采集失败：{image_name}")

    def refresh_goods(self):
        button = 'refresh.png'
        self.find_and_click(button)

    def execute(self):
        url = None
        image_list = []
        time.sleep(1)
        self.set_progress_top()
        self.turn_on_collect()
        point = 'pulling.png'
        while self.is_collect:
            for j in range(11):
                res, location = self.check_point(point, confidence=0.8, t=0.3, times=1)
                if not location:
                    break
                time.sleep(2)
                if j > 9:
                    log.error('pp Work撞库卡数据，程序运行结束')
                    return
            try:
                image_list, url = self.download_image1(image_list, url=url)
            except ImportError:
                continue
            self.mouse_click(x=cg.x, y=cg.y)
            if not image_list:
                self.mouse_scroll(-5)
                continue

            if len(image_list) > 7:
                image_list.pop(0)
            self.collect_data(image_list)
            log.info(f'{self.pull_data_path}循环第{n}次')
        log.info('*' * 20 + '采集结束' + '*' * 20)
        print('*' * 20 + '采集结束' + '*' * 20)

    def execute1(self):
        self.refresh_goods()
        nn = n1 = n2 = 0
        is_re = False
        url = None
        image_list = []
        value1 = None
        if cg.extend is False:
            self.kill_task()
            self.start_task()
            pyautogui.click(cg.x, cg.y)
            self.get_pull_data()

        time.sleep(1)
        self.set_progress_top()
        self.turn_on_collect()

        for n in range(cg.num):
            if len(image_list) > cg.goods_list:
                if is_re:
                    self.mouse_scroll((n - n2) * 6 + 30)
                    is_re = False
                    n1 = n2
                    n2 = n
                if n - n2 >= (n2 - n1)*2:
                    is_re = True
            elif len(image_list) > cg.goods_max:
                print('*'*20 + '采集结束' + '*'*20)
                return
            point = 'pulling.png'
            res, location = self.check_point(point, confidence=0.8, t=0.3, times=1)
            print('正在撞库。。。')
            if location:
                time.sleep(2)
                continue
            image_list, url = self.download_image1(image_list, url=url)
            if n == 0 and cg.extend:
                image_list = []
            if n % 10 == 0:
                self.mouse_click(x=cg.x, y=cg.y)
                nn += 1
                if nn == 3:
                    try:
                        if value1 == image_list[0]:
                            image_list.pop(0)
                        value1 = image_list[0]
                        nn = 0
                    except IndexError:
                        pass
            self.collect_data(image_list)
        print('*' * 20 + '采集结束' + '*' * 20)

    def find_image_on_screen_windows(self, image):
        template_path = "image/%s" % image
        try:
            location = self.find_image_on_screen(template_path, confidence=0.8)
            x, y = location
            button = cg.button
            self.collector_find_and_click(button)
            self.mouse_click(x=x, y=y)
            res, loc = self.check_point('collect.png')
            if loc:
                print("进入商品详情页")
                return location
            else:
                log.error('检测到点击商品后没有进入商品详情页，有可能被风控，程序暂停')
                print('检测到点击商品后没有进入商品详情页，有可能被风控，程序暂停')
                while not loc:
                    time.sleep(10)
                    res, loc = self.check_point('collect.png')
                    if loc:
                        log.info("检测到已经进入商品详情页，程序继续")
                        print("检测到已经进入商品详情页，程序继续")
                        return location
        except:
            print("未找到图像")
            return None

    def get_handle(self, title=None):
        """根据程序title寻找句柄"""
        handle = win32gui.FindWindow(None, title)
        if handle == 0:
            raise Exception("can not find windows of handle!")
        return handle

    def set_window_always_on_top(self, handle=None, title=None):
        """
        设置窗口始终在最前
        """
        # 使用 SetWindowPos 将窗口置于顶层
        win32gui.SetWindowPos(handle, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        print(f"窗口 {title} 已设置为始终在最前")

    def mouse_scroll(self, clicks):
        """
        模拟鼠标滚轮滚动
        :param clicks: 正数向上滚动，负数向下滚动
        """
        ctypes.windll.user32.mouse_event(
            self.MOUSEEVENTF_WHEEL,
            0,  # x位置
            0,  # y位置
            clicks * 120,  # 120是Windows定义的WHEEL_DELTA
            0  # 额外信息
        )

    def mouse_click(self, x=None, y=None, button='left', double=False):
        """
        模拟鼠标点击
        :param button: 鼠标按钮 ('left', 'right', 'middle')
        :param x: 目标X坐标 (None表示当前位置)
        :param y: 目标Y坐标 (None表示当前位置)
        :param double: 是否双击
        """
        # 如果需要移动到指定位置
        if x is not None and y is not None:
            ctypes.windll.user32.SetCursorPos(x, y)

        # 确定按钮类型
        if button == 'left':
            down = self.MOUSEEVENTF_LEFTDOWN
            up = self.MOUSEEVENTF_LEFTUP
        elif button == 'right':
            down = self.MOUSEEVENTF_RIGHTDOWN
            up = self.MOUSEEVENTF_RIGHTUP
        elif button == 'middle':
            down = self.MOUSEEVENTF_MIDDLEDOWN
            up = self.MOUSEEVENTF_MIDDLEUP
        else:
            raise ValueError("button参数必须是'left', 'right'或'middle'")

        # 执行点击
        ctypes.windll.user32.mouse_event(down, 0, 0, 0, 0)
        ctypes.windll.user32.mouse_event(up, 0, 0, 0, 0)

        # 如果是双击，再次点击
        if double:
            time.sleep(0.1)  # 双击之间的短暂延迟
            ctypes.windll.user32.mouse_event(down, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(up, 0, 0, 0, 0)

    def remove_empty_folders(self):
        """递归删除所有空文件夹"""
        today = datetime.today().date()
        path = os.path.join(os.getcwd(), 'pull_data', str(today))
        for root, dirs, files in os.walk(path, topdown=False):
            for folder in dirs:
                folder_path = os.path.join(root, folder)
                try:
                    if not os.listdir(folder_path):  # 如果文件夹为空
                        os.rmdir(folder_path)  # 删除空文件夹
                        print(f"已删除空文件夹: {folder_path}")
                except (PermissionError, OSError) as e:
                    print(f"无法删除 {folder_path}: {e}")

    def upload_collect_file(self):
        buttons = ['upload_result.png', 'pull_task_login_id.png', 'original_file.png', 'result_file.png', 'pp_start.png']
        for button in buttons:
            res, location = self.check_point(button)
            if location:
                x, y = location
                self.mouse_click(x=x, y=y)
                time.sleep(1)
                match button:
                    case 'pull_task_login_id.png':
                        keyboard.write(cg.pp_login_id)
                    case 'original_file.png':
                        try:
                            file_name = os.path.join(self.pull_data_path, self.file)
                        except:
                            log.error('找不到excel文件，上传失败')
                            raise Exception('找不到excel文件，上传失败')
                        keyboard.write(file_name)
                    case 'result_file.png':
                        import zipfile
                        file = self.get_files_sorted_by_mtime(self.pull_data_path)[0]
                        zip_path = os.path.join(self.pull_data_path, file)
                        extract_dir = os.path.join(self.pull_data_path, file.split('.')[0])

                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_dir)

                        keyboard.write(extract_dir)
        for x in range(10):
            image = 'upload_over.png'
            res, location = self.check_point(image)
            time.sleep(10)
            if location:
                return
        file_path = os.path.join(os.getcwd(), 'not_upload.txt')
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(self.pull_data_path + '\n')
            f.close()


if __name__ == '__main__':
    # test = PPCollect()
    # test.remove_empty_folders()
    # test.return_back_home()
    test = PPCollect()
    for i in range(cg.counts):
        # log.info('*'*25 + f'开始第{i+1}次采集副本' + '*'*25)
        test.setup_collect()
        try:
            test.execute()
        except pywintypes.error:
            log.error(traceback.format_exc())
            print(traceback.format_exc())
            continue
        except:
            log.error(traceback.format_exc())
            print(traceback.format_exc())
        finally:
            test.teardown_collect()
            test.remove_empty_folders()

