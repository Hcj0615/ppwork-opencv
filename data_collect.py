import os
import traceback
import pandas as pd

import cv2
import keyboard
import numpy as np
import pyautogui
import time

import mss
import pyperclip
import win32con
import win32gui
import win32process
import psutil
from PIL import Image

from selenium import webdriver

import config_collect as cg
from openpyxl import load_workbook

from get_image import download_image


class AutoZombie:
    def __init__(self, num=100):
        self.hwnd = None
        self.scale = 1
        self.is_match = False
        self.num = num
        self.driver = None
        self.f = None
        self.title = cg.bluestacks
        self.workbook = load_workbook(filename=cg.file_name)
        self.set_up_execute()

    def login_pdd(self):
        self.driver.get('https://mobile.yangkeduo.com/login.html')        # 点击手机登录按钮
        ele = self.driver.find_element(by='xpath', value='//span[contains(text(), "手机登录")]')
        ele.click()
        # 输入手机号码
        ele = self.driver.find_element(by='id', value='user-mobile')
        phone = input("登录拼多多，请输入手机号:")
        ele.send_keys(phone)
        # 点击发送验证码按钮
        ele = self.driver.find_element(by='id', value='code-button')
        ele.click()
        # 输入验证码
        ele = self.driver.find_element(by='id', value='input-code')
        code = input("登录拼多多，请输入验证码:")
        ele.send_keys(code)
        # 点击同意协议
        ele = self.driver.find_element(by='xpath', value='//i[@class]')
        ele.click()
        # 点击登录按钮
        ele = self.driver.find_element(by='id', value='submit-button')
        ele.click()
        time.sleep(2)

    def set_up_execute(self):
        if os.path.exists(cg.transform_file):  # 检查文件是否存在
            os.remove(cg.transform_file)  # 删除文件
        if os.path.exists(cg.uncollect_file):  # 检查文件是否存在
            os.remove(cg.uncollect_file)  # 删除文件

    def tear_down_execute(self):
        self.workbook.save(cg.file_name)
        self.workbook.close()
        # self.driver.quit()
        self.cancel_always_on_top()

    def match_screen(self, img):
        if self.is_match:
            return cv2.resize(img, None, fx=self.scale, fy=self.scale)
        else:
            return img

    def get_progress_screen(self, handle=None):
        """获取进程窗口，并置最前"""
        if handle:
            self.hwnd = handle
        else:
            self.get_handle()
        self.set_window_always_on_top()
        self.get_screen_scale()

    def get_screen_scale(self):
        """获取进程窗口区域比例"""
        _, rect = self.get_handle_windows_screen()
        x1, y1, x2, y2 = rect
        height = y2 - y1
        width = x2 - x1
        self.scale = width / 582

        print(f"目标进程窗口长宽：{height} x {width}")
        if self.scale != 1:
            self.is_match = True

    # 获取多显示器信息，并截取指定显示器的图片
    def screenshot_monitor_region(self, region):
        """
        截取指定显示器的特定区域
        :param region: 截图区域，格式为 (left, top, width, height)
        """
        with mss.mss() as sct:
            # 计算绝对坐标
            left = region[0]
            top = region[1]
            width = region[2]
            height = region[3]

            # 截图
            screenshot = sct.grab({'left': left, 'top': top, 'width': width, 'height': height})

            # 转换为 PIL 图像并保存
            screenshot = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            return screenshot

    def set_window_always_on_top(self, handle=None, title=None):
        """
        设置窗口始终在最前
        """
        if not handle:
            handle = self.hwnd
        if not title:
            title = self.title
        # 使用 SetWindowPos 将窗口置于顶层
        win32gui.SetWindowPos(handle, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        print(f"窗口 {title} 已设置为始终在最前")

    def cancel_always_on_top(self):
        """
        取消窗口始终在最前的设置
        """
        # 使用 SetWindowPos 恢复窗口的默认 Z 顺序S
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        print(f"窗口 {self.title} 的始终在最前设置已取消")

    def get_handle(self, title=None):
        """根据程序title寻找句柄"""
        if not title:
            title = self.title
        self.hwnd = win32gui.FindWindow(None, title)
        if self.hwnd == 0:
            raise Exception("can not find windows of handle!")
        return self.hwnd

    def get_handle_by_progress(self, progress):
        """根据进程名称查询句柄"""
        def callback(hwnd, handles):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    if proc.name() == progress:
                        handles.append(hwnd)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return True

        handles = []
        win32gui.EnumWindows(callback, handles)
        return handles[0] if handles else None

    def get_handle_windows_screen(self):
        """获取进程区域坐标和截图"""
        screen_width, _ = pyautogui.size()
        rect = win32gui.GetWindowRect(self.hwnd)
        x1, y1, x2, y2 = rect
        region = [x1, y1, x2 - x1, y2 - y1]
        screenshot = self.screenshot_monitor_region(region)
        # screenshot.save(f"input0.png")
        return screenshot, rect

    def get_center_point(self):
        """寻找窗口中心点"""
        rect = win32gui.GetWindowRect(self.hwnd)
        x1, y1, x2, y2 = rect
        center_x = (x2 + x1) / 2
        center_y = (y2 + y1) / 2
        return center_x, center_y

    def find_image_on_screen(self, template_path, confidence=0.8):
        """
        在屏幕上查找指定的图片。
        :param template_path: 模板图片的路径
        :param confidence: 匹配置信度（0到1之间）
        :return: 如果找到图片，返回其中心坐标；否则返回None
        """
        screenshot, rect = self.get_handle_windows_screen()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 读取模板图片
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        # cv2.imshow('Image', template)
        # cv2.waitKey(0)  # 等待任意按键关闭窗口
        # cv2.destroyAllWindows()

        # 使用模板匹配
        # template = self.match_screen(template)
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 如果匹配度高于置信度，则返回中心坐标
        screen_x, screen_y, _, _ = rect
        if max_val >= confidence:
            template_height, template_width = template.shape[:2]
            center_x = max_loc[0] + screen_x + template_width // 2
            center_y = max_loc[1] + screen_y + template_height // 2

            return center_x, center_y
        else:
            return None

    def find_image_on_screen_windows(self, image):
        template_path = "image/%s" % image
        try:
            location = pyautogui.locateOnScreen(template_path)
            x, y = location
            pyautogui.click(x, y)
            print("找到图像位置:", location)
            return location
        except pyautogui.ImageNotFoundException:
            print("未找到图像")
            return None

    # 设置检测点
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

    def get_data_from_excel(self):
        file_path = os.path.join(os.getcwd(), 'pull_data')
        files = self.get_files_sorted_by_mtime(file_path)
        file = files[0]
        return pd.read_excel(file)

    def get_files_sorted_by_mtime(self, directory):
        # 获取目录下所有文件和子目录
        entries = [os.path.join(directory, f) for f in os.listdir(directory)]

        # 过滤出文件（排除目录）
        files = [f for f in entries if os.path.isfile(f)]

        # 按修改时间排序（最新的在前）
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        return files

    def get_column_data_from_excel(self, column=8):
        """读取excel指定列"""
        # 选择工作表
        sheet = self.workbook["Sheet1"]  # 或 workbook.active 获取活动工作表
        cell_value = '11'
        value_list = []
        i = 2
        while cell_value:
            # 获取指定单元格数据
            cell_value = sheet.cell(row=i, column=column).value  # 通过行列号
            value_list.append(cell_value)
            i += 1

        return value_list

    def write_into_excel(self, data, column="I"):
        """将转换后的url写入excel指定列"""
        # 选择工作表
        sheet = self.workbook["Sheet1"]  # 或 workbook.active 获取活动工作表

        # 2. 定义要写入的数据（列表或字典）
        # data = ["数据1", "数据2", "数据3"]  # 要写入的数据
        column_letter = column  # 指定列（例如 B 列）

        # 3. 写入数据到指定列
        for i, value in enumerate(data, start=2):  # start=1 表示从第 1 行开始
            sheet[f"{column_letter}{i}"] = value  # 如 B1, B2, B3...

        # 4. 保存文件
        self.workbook.save(cg.file_name)
        print(f"数据已写入 {cg.file_name} 的 {column_letter} 列")

    def get_browser(self, value):
        # 打开网页
        self.driver.get(value)
        # 获取页面标题
        print(self.driver.title)

    def move_mouse_to(self):
        # 等待 2 秒，方便用户切换到目标窗口
        time.sleep(0.5)
        pic_path = "data/qq.png"
        try:
            start_x, start_y = self.find_image_on_screen(pic_path)
        except TypeError:
            return
        # 文件目标位置
        end_x, end_y = start_x - 300, start_y
        # 移动鼠标到文件起始位置
        pyautogui.moveTo(start_x, start_y)
        # 按下鼠标左键
        pyautogui.mouseDown()
        # 拖动文件到目标位置，耗时 1 秒
        pyautogui.moveTo(end_x, end_y, duration=1)
        # 释放鼠标左键
        pyautogui.mouseUp()

    def write_transform_url(self, text, file_name=cg.transform_file):
        """将转换后的url写入txt文件"""
        with open(file_name, 'a', encoding='utf-8') as self.f:
            self.f.write(text + '\n')

    def open_wechat_browser(self):
        """打开微信小程序"""
        import uiautomation as auto
        # 获取微信窗口
        wechat_window = auto.WindowControl(Name="微信")
        if wechat_window.Exists():
            # 模拟点击「浏览器」按钮（需自行定位控件）
            browser_btn = wechat_window.ButtonControl(Name="小程序面板")
            browser_btn.Click()
        else:
            print("微信未运行")

    def collect_by_browser(self, value_list):

        self.title = cg.collect_title
        self.get_progress_screen()
        self.login_pdd()
        for url in value_list:
            if 'http' not in url:
                try:
                    int(url)
                    url = f'https://mobile.yangkeduo.com/goods.html?goods_id={url}&_oak_rcto=YWKIVYwrSM4Yt2yq8B8DKzkKvM_R8dDxuLPduCPmARnHmyYv4Jc1rr76&_oak_gallery=https%3A%2F%2Fimg.pddpic.com%2Fmms-material-img%2F2024-11-27%2Fd384dcbb-039e-49f5-933b-71b5d3e98199.jpeg.a.jpeg&_oak_gallery_token=9e65eeb3a19a8f3d79e5100984a35173&_oc_refer_ad=0&_x_query=%E3%80%901097%E4%BA%BA%E6%94%B6%E8%97%8F%E3%80%91%E5%A4%A9%E5%9C%B0%E9%B1%BC%E5%90%B8%E7%9B%98%E6%AF%9B%E5%B7%BE%E6%9E%B6%E5%8D%AB%E7%94%9F%E9%97%B4%E5%85%8D%E6%89%93%E5%AD%94%E6%B5%B4%E5%B7%BE%E7%BD%AE%E7%89%A9%E6%9E%B6%E5%AD%90%E4%B8%80%E4%BD%93%E6%B5%B4%E5%AE%A4%E5%8E%95%E6%89%80%E6%8C%82%E6%9D%86%E5%A5%97%E4%BB%B6&refer_page_el_sn=99369&refer_rn=&page_from=23&refer_page_name=search_result&refer_page_id=10015_1753586975000_brr9njolix&refer_page_sn=10015&uin=QKEQYYBZCFKY6L76C4KFPFQLVM_GEXDA'
                except:
                    continue
            self.get_browser(url.strip())

            time.sleep(2)
            button = cg.button
            result, location = self.check_point(button, confidence=0.8, times=2)

            if not result:
                print('没有采集到数据：', url)
                self.write_transform_url(url, file_name='not_collect.txt')
                continue

            x, y = location
            pyautogui.click(x, y)
            pyautogui.moveTo(cg.close_x, cg.close_y)
        print('结束')
        return

    def execute_collect_by_browser(self):
        """chrome浏览器执行采集"""
        self.driver = webdriver.Chrome()
        value_list = self.get_column_data_from_excel(column=2)
        self.collect_by_browser(value_list)

    def execute_transform_by_app(self):
        """拼多多app转换url-雷电模拟器"""
        value_list = self.get_column_data_from_excel()
        self.transform_url_list_by_app(value_list)

    def execute_collect_by_weixin_browser(self):
        """使用微信浏览器执行采集"""
        value_list = self.get_column_data_from_excel()
        progress = 'WeChatAppEx.exe'
        handle = self.get_handle_by_progress(progress)
        self.collect_by_weixin_browser(value_list, handle)

    def execute_collect(self):
        """app转换url后，用微信浏览器执行采集"""
        value_list = self.get_column_data_from_excel(column=7)
        value_list_transform = self.transform_url_list_by_app(value_list)
        progress = 'WeChatAppEx.exe'
        handle = self.get_handle_by_progress(progress)
        self.collect_by_weixin_browser(value_list_transform, handle)

    def collector_find_and_click(self, url):
        """监控采集器的确认添加按钮"""
        button = cg.button
        result, location = self.check_point(button, confidence=0.8, times=2)

        if not result:
            print('没有采集到数据：', url)
            self.write_transform_url(url)
            return

        x, y = location
        pyautogui.click(x, y)
        pyautogui.moveTo(cg.close_x, cg.close_y)

    def collect_by_weixin_browser(self, url_list, handle):
        """微信浏览器执行url采集"""
        self.title = cg.collect_title
        for url in url_list:
            self.get_progress_screen(handle=handle)
            button_list = ['search.png', 'input_url.png']
            for button in button_list:
                result, location = self.check_point(button, times=2)
                if not result:
                    print('没有找到：', button)
                    break
                match button:
                    case 'search.png':
                        x, y = location
                        pyautogui.click(x, y)
                    case 'input_url.png':
                        keyboard.write(url, delay=0.01)
                        pyautogui.press('enter')  # 按回车键

            self.get_progress_screen()
            self.collector_find_and_click(url)
        print("end")

    def get_home_page(self):
        """雷电模拟器返回主页-自动化执行一半失败时可以纠正"""
        button_list = ['home1.png', 'browser_app.png']
        for button in button_list:
            result, location = self.check_point(button, times=2)
            if not result:
                print('没有找到：', button)
                break

            x, y = location
            pyautogui.click(x, y)

    def transform_url_list_by_app(self, value_list):
        """用拼多多app转换列表内的url"""
        value_list_transform = list()
        self.title = cg.bluestacks
        self.get_progress_screen()
        for value in value_list:
            if not value:
                break
            pyperclip.copy('')
            url = self.transform_url_by_app(value)
            self.write_transform_url(url)
            self.f.close()
            value_list_transform.append(url)
        self.write_into_excel(value_list_transform)
        return value_list_transform

    def transform_url_by_app(self, value):
        """用拼多多app转换url-雷电模拟器"""
        button_list = ['home.png', 'browser.png', 'https.png', 'open_in_app.png', 'share.png', 'copy_url.png']
        for button in button_list:
            if button == 'copy_url.png':
                self.move_mouse_to()
            result, location = self.check_point(button, times=2)
            if not result:
                print('没有找到：', button)
                self.get_home_page()
                # self.transform_url_by_app(value)
                print('转换前的url:', value)
                print('转换后的url:', '售空')
                return '售空'

            x, y = location
            pyautogui.click(x, y)
            if button == 'https.png':
                # 输入字符串并立即按回车
                # value = 'https://mobile.yangkeduo.com/goods.html?goods_id=628377999504'
                keyboard.write(value, delay=0.01)
                pyautogui.press('enter')  # 按回车键goods.htm
                pyautogui.press('enter')  # 按回车键goods.htm
                time.sleep(0.5)
        text = pyperclip.paste()
        for i in range(2):
            text = pyperclip.paste()
            # time.sleep(1)
        print('转换前的url:', value)
        print('转换后的url:', text)
        return text

    def find_and_click(self, image_path, confidence=0.8):
        """在屏幕上查找图片并点击中心位置"""
        try:
            # 查找图片在屏幕上的位置
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location is not None:
                # 计算中心坐标
                center = pyautogui.center(location)
                # 移动并点击
                pyautogui.moveTo(center)
                pyautogui.click()
                print(f"找到图片 {image_path} 并点击位置 {center}")
                return True
            else:
                print(f"未找到图片 {image_path}")
                return False
        except Exception as e:
            print(f"查找图片时出错: {e}")
            return False

    def get_data_counts(self):
        return len(self.get_data_from_excel())

    def download_image(self):
        save_path = os.path.join(os.getcwd(), 'image')
        df = self.get_data_from_excel()
        url_list = df['image_url']
        image_list = []
        for url in url_list:
            image_name = f'image{url[-10: -5]}.png'
            save_image = os.path.join(save_path, image_name)
            result = download_image(url, save_image)
            if result:
                image_list.append(image_name)
        return image_list

    def get_pull_data(self):
        pyautogui.click(cg.x, cg.y)
        is_pull = 'pull_data.png'
        for j in range(1000):
            pyautogui.press('down', presses=15)
            time.sleep(3)
            # for i in range(30):
            #     pyautogui.press('down', presses=15)
            #     time.sleep(5)
            #     if i > 25:
            #         time.sleep(1)
            #         result, location = self.check_point(is_pull, times=2)
            #         if result:
            #             time.sleep(5)
            #             break

    def execute(self):
        # handle_pp = self.get_handle(title='PP WORK')
        # self.set_window_always_on_top(handle=handle_pp, title='PP WORK')
        handle_collect = self.get_handle(title=cg.collect_title)
        self.set_window_always_on_top(handle=handle_collect, title=cg.collect_title)
        # self.get_pull_data()
        image_list = self.download_image()
        for i in range(1000):
            for index, image_name in enumerate(image_list):
                result = self.find_image_on_screen_windows(image_name)
                self.collector_find_and_click1(image_name)
                pyautogui.click(cg.x, cg.y)
                if result:
                    try:
                        image_list.pop(index)
                    except IndexError:
                        print('图片全部采集完成')
                        return
            pyautogui.press('up', presses=15)

    def collector_find_and_click1(self, image):
        """监控采集器的确认添加按钮"""
        button = cg.button
        result, location = self.check_point(button, confidence=0.8, times=2)

        if not result:
            print('没有采集到数据：', image)
            return

        x, y = location
        pyautogui.click(x, y)
        pyautogui.moveTo(cg.close_x, cg.close_y)


if __name__ == "__main__":
    # aa = input("请选择采集方式(浏览器1，app转化2，app转化后微信浏览器3):\n")
    test = AutoZombie(num=10000)
    # test.get_pull_data()
    test.execute()
    # try:
    #     match aa:
    #         case '1':
    #             test.execute_collect_by_browser()
    #         case '2':
    #             test.execute_transform_by_app()
    #         case '3':
    #             test.execute_collect()
        # test.transform_url_by_app('https://mobile.yangkeduo.com/goods.html?goods_id=628377999504')
    # except:
    #     print(traceback.format_exc())
    # finally:
    #     test.tear_down_execute()
