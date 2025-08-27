import asyncio
import threading
import time

import pyautogui

from pp_collect import PPCollect
import config_collect as cg


test = PPCollect()


def set_goods_position():
    point = 'data\\yuan.png'
    matches = test.find_multiple_matches(point)
    test.mouse_click(x=cg.x, y=cg.y)
    while len(matches) < 4:
        print('调整商品位置，便于比对观察')
        pyautogui.press('down', presses=1)
        matches = test.find_multiple_matches(point)


def get_image_list(image_list, url, is_get=True):
    while is_get is True:
        image_list, url = test.download_image1(image_list, url=url)
        time.sleep(10)


def back_home():
    test.return_back_home()


def collect(image_list):
    for index, image_name in enumerate(image_list):
        result = test.find_image_on_screen_windows(image_name)
        if result:
            button = cg.button
            test.collector_find_and_click(button)
            try:
                image_list.pop(index)
            except IndexError:
                print('图片全部采集完成')
                return
            finally:
                break
        else:
            print("没有采集到：", image_name)


def execute_collect():
    test.turn_on_collect()
    handle_pp = test.get_handle(title='PP WORK')
    test.set_window_always_on_top(handle=handle_pp, title='PP WORK')
    handle_collect = test.get_handle(title=cg.collect_title)
    test.set_window_always_on_top(handle=handle_collect, title=cg.collect_title)
    test.get_pull_data()
    url = None
    is_get = True
    image_list = []
    t = threading.Thread(target=get_image_list, args=(image_list, url, is_get))
    t.start()
    for n in range(100):
        test.return_back_home()
        test.mouse_click(x=cg.x, y=cg.y)
        print('向下移动一个商品位置')
        test.mouse_scroll(-5)
        set_goods_position()

        back_home()
        collect(image_list)
        print(image_list)
        # image_list = self.get_image_list_from_dir()
        # image_list = ['image38e13.png']
    is_get = False
    t.join()

execute_collect()
