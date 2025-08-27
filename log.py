# !/usr/bin/env python
# coding: utf-8
"""
__author__ = 'huangchangjing'

整个工程的打印方法，RF的HTML显示以及本地保存单独的txt日志文件。
"""


import json
import os
import time
from datetime import datetime
from robot.api import logger


class Logger(object):
    file_path = None
    file_name = None

    file_count = 0  # 分割保存的文件数量索引
    file_size = 8 * 1024 ** 2  # 单个文件保存最大参考值(MB)
    total_invoke_times = 0  # log方法调用的写入次数，用于判断是否检查日志文件大小

    _file_obj = None
    _file_obj_ids = list()  # 记录有日志文件操作对象ID

    def __init__(self):
        self.current_time = time.strftime('%Y%m%d%H%M%S')
        self.file_name = f'RF_Local_Log_{self.current_time}_{self.file_count}.txt'
        self.file_path = self._get_log_path(self.file_name)
        self._file_obj = open(self.file_path, 'a')
        self._file_obj_ids.append(id(self._file_obj))

    def delete_old_log(self):
        """删除超过30天的日志"""
        # 获取当前目录
        dir_path = self._get_project_root_path()
        dir_path = os.path.join(dir_path, 'Log')
        for filename in os.listdir(dir_path):
            try:
                file_update_time = filename.split('_')[3]
            # 忽略非日志文件
            except IndexError:
                continue

            file_path = os.path.join(dir_path, filename)
            # 判断类型是否为文件
            if os.path.isfile(file_path):
                # 判断文件创建时间大于30天
                if int(self.current_time) - int(file_update_time) > 30*1000000:
                    # 删除
                    os.remove(file_path)

    def _get_log_path(self, file_name):
        """
        - 获取日志文件的绝对路径
        :param file_name: 日志文件名称
        :return: 绝对路径
        """
        # project_root = self._get_project_root_path()
        log_path = os.path.join(os.getcwd(), 'Log')
        if not os.path.exists(log_path):
            os.mkdir(log_path)
            print('Log目录不存在，新建目录。')
        file_abs_path = os.path.join(log_path, file_name)
        return file_abs_path

    @staticmethod
    def _get_project_root_path():
        """
        - 获取当前项目的根路径
        :return: 当前工程的根路径
        """
        path = os.path.dirname(__file__)
        split1 = 'E_Pylibs'
        if split1 in path:
            path = path.split(split1)[0]
        return os.path.split(path)[0]

    def write_to_file(self, msg, level='DEFAULT'):
        """
        - 写日志信息到文件上
        :param msg: 日志信息
        :param level: 日志等级
        """
        # 一般情况下，不会关闭的。除非调用过save_log_file，保存日志文件的方法。
        if self._file_obj.closed:
            self._file_obj = open(self.file_path, 'a')
            _msg = '{} [{}]: {}\n'.format(
                datetime.now().strftime('%Y-%m-%d %X.%f')[:-3], 'DEFAULT', '没有打开日志文件操作对象，重新打开最新的日志文件！'
            )
            self._file_obj.write(_msg)
        # 写入日志数据
        msg = '{} [{}]: {}\n'.format(datetime.now().strftime('%Y-%m-%d %X.%f')[:-3], level, msg)
        self._file_obj.write(msg)
        # 统计下日志写入调用的次数
        self._record_invoke_times()

    def _record_invoke_times(self):
        """
        - 调用写入文件方法若干次后，判断下文件大小。
        - 如果超过设定的单个日志文件大小，则新建一个日志文件。
        """
        self.total_invoke_times += 1
        if self.total_invoke_times % 30 == 0:
            # 判断下当前日志文件大小，如果太大了，日志文件拆开。
            size = os.path.getsize(self.file_path)
            if size > self.file_size:
                self._create_new_log_file()

    def _create_new_log_file(self):
        # 产生新的一个日志文件名称
        self.file_count += 1
        _tmp_name = self.file_name.split('_')
        _tmp_name[-1] = '{}.txt'.format(self.file_count)
        self.file_name = '_'.join(_tmp_name)
        self.file_path = self._get_log_path(self.file_name)
        log.tip('当前日志文件容量较大，新建一个日志文件保存数据！路径为：{}'.format(self.file_path))
        # 清空缓存区
        self._file_obj.flush()
        # 关闭当前日志文件
        self._file_obj.close()
        # 打开新的日志文件
        self._file_obj = open(self.file_path, 'a')
        self._file_obj_ids.append(id(self._file_obj))

    def save_log_file(self):
        """
        - 建议在全局teardown的时候，调用这个方法手动关闭下打开的文件。
        """
        self.tip('#' * 100)
        self.tip('即将关闭打开的日志文件，保存日志数据。日志写入的方法调用次数为{}次！当前所有的文件操作对象ID为：{}'
                 .format(self.total_invoke_times, self._file_obj_ids))
        self.tip('#' * 100)
        self._file_obj.flush()
        self._file_obj.close()

    def debug(self, msg):
        msg = self._check_msg_size_and_write_info(msg, 'DEBUG', 'orange')
        # TODO 这个由于hippo的等级信息最低是Info，这边兼容下改成info级别，否则很多调试信息没法看到。
        logger.info(msg, html=True)

    def info(self, msg):
        msg = self._check_msg_size_and_write_info(msg, 'INFO', 'blue')
        logger.info(msg, html=True)

    def warn(self, msg):
        msg = self._check_msg_size_and_write_info(msg, 'WARN', 'brown')
        logger.warn(msg, html=True)

    def error(self, msg):
        msg = self._check_msg_size_and_write_info(msg, 'ERROR', 'red')
        logger.error(msg, html=True)

    def tip(self, msg, color='purple'):
        msg = self._check_msg_size_and_write_info(msg, 'TIP', color)
        logger.info('{}{}{}'.format('<b>', msg, '</b>'), html=True)

    def ok(self, msg):
        msg = self._check_msg_size_and_write_info(msg, 'OK', 'green')
        logger.info(msg, html=True)

    def fail(self, msg):
        msg = self._check_msg_size_and_write_info(msg, 'FAIL', 'red')
        logger.error(msg, html=True)

    def raw_info(self, msg, html=False):
        msg = self._check_msg_size_and_write_info(msg, 'INFO', html=html)
        logger.info(msg, html=html)

    def _check_msg_size_and_write_info(self, msg, level, color='black', html=True):
        if not isinstance(msg, str):
            try:
                msg = json.dumps(msg, ensure_ascii=False)
            except:  # json.dumps有可能序列化失败，报错xxx is not JSON serializable，这里先不处理
                pass
        size = 20480  # 字符长度
        # 先写入到本地文件中
        self.write_to_file(msg, level)
        if len(repr(msg)) > size:
            msg = '【要打印的信息内容太长:{} 大于 {}，不在RF上打印，直接保存在本地日志文件中:{}】' \
                .format(len(msg), size, log.file_path)
        # 如果是需要HTML展示的，则再封装下
        if html:
            msg = '<span style="color:{}">{}</span>'.format(color, msg)
        return msg


log = Logger()


if __name__ == '__main__':
    log = Logger()
    log.delete_old_log()
