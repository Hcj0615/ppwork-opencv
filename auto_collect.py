import sys
import traceback
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit,
                             QPushButton, QVBoxLayout, QWidget, QLabel,
                             QLineEdit, QHBoxLayout)
from PyQt5.QtCore import pyqtSignal, QThread
from log import log


class Worker(QThread):
    """工作线程，用于在后台运行主函数"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, args):
        super().__init__()
        self.args = args
        self._is_running = True

    def run(self):
        """执行目标函数"""
        old_stdout = sys.stdout
        sys.stdout = self
        print("开始采集...")
        from pp_work_collect import PPCollect
        test = PPCollect()
        if 'collect_counts' in self.args:
            num = int(self.args['collect_counts'])
        else:
            num = test.config['collect_counts']

        if 'get_data_num' in self.args:
            test.get_data_num = int(self.args['get_data_num'])
        else:
            test.get_data_num = test.config['get_data_num']
        for z in range(num):
            # log.info('*'*25 + f'开始第{i+1}次采集副本' + '*'*25)
            try:
                test.setup_collect()
                test.execute()
            except Exception as e:
                self.error_signal.emit(f"[ERROR] 执行失败: {str(e)}\n{traceback.format_exc()}")
                log.error(traceback.format_exc())
                print(traceback.format_exc())
            finally:
                test.teardown_collect()
                sys.stdout = old_stdout
                self._is_running = False
                self.finished_signal.emit()
        # 主要业务逻辑...
        print("自动化采集完成")
        # try:
        #     # 动态导入模块（相对导入）
        #     module = __import__(TARGET_MODULE, fromlist=[TARGET_FUNCTION])
        #     func = getattr(module, TARGET_FUNCTION)
        #
        #     # 重定向标准输出
        #     old_stdout = sys.stdout
        #     sys.stdout = self
        #
        #     # 调用函数
        #     if self.args:
        #         func(**self.args)
        #     else:
        #         func()
        #
        # except Exception as e:
        #     self.error_signal.emit(f"[ERROR] 执行失败: {str(e)}\n{traceback.format_exc()}")
        # finally:
        #     sys.stdout = old_stdout
        #     self._is_running = False
        #     self.finished_signal.emit()

    def write(self, text):
        """捕获print输出"""
        if self._is_running:
            self.output_signal.emit(text.strip())

    def flush(self):
        pass


class PythonRunner(QMainWindow):
    def __init__(self):
        super().__init__()
        # 设置窗口图标（同时影响任务栏图标）
        self.setWindowIcon(QIcon('auto_ui.ico'))

        # 设置窗口标题
        self.setWindowTitle("工程控制系统")

        # 然后添加其他组件
        self.setup_ui()
        self.worker = None

    def setup_ui(self):
        """初始化UI组件"""
        self.setWindowTitle("自动化采集控制台")
        self.setGeometry(100, 100, 800, 600)

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # 参数输入区域
        param_layout = QVBoxLayout()

        # 参数1输入
        param1_layout = QHBoxLayout()
        param1_layout.addWidget(QLabel("输入单次采集数量:"))
        self.param1_input = QLineEdit()
        self.param1_input.setPlaceholderText("可不填，默认 100")
        param1_layout.addWidget(self.param1_input)
        param_layout.addLayout(param1_layout)

        # 参数2输入
        param2_layout = QHBoxLayout()
        param2_layout.addWidget(QLabel("输出采集循环次数:"))
        self.param2_input = QLineEdit()
        self.param2_input.setPlaceholderText("可不填，默认 2")
        param2_layout.addWidget(self.param2_input)
        param_layout.addLayout(param2_layout)

        layout.addLayout(param_layout)

        # 输出显示区
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("运行日志将显示在这里...")
        layout.addWidget(self.log_output)

        # 按钮布局
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        # 运行按钮
        self.run_button = QPushButton("运行 (F5)")
        self.run_button.clicked.connect(self.safe_run_function)
        self.run_button.setShortcut("F5")
        button_layout.addWidget(self.run_button)

        # 停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_function)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        # 清空按钮
        self.clear_button = QPushButton("清空输出")
        self.clear_button.clicked.connect(self.log_output.clear)
        button_layout.addWidget(self.clear_button)

    def safe_run_function(self):
        """安全执行函数（捕获所有异常）"""
        try:
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.log_output.clear()

            # 解析参数
            args = {}
            if self.param1_input.text():
                args["get_data_num"] = self.param1_input.text()
            if self.param2_input.text():
                args["collect_counts"] = self.param2_input.text()

            self.log_output.append("> 开始运行工程...")
            if args:
                self.log_output.append(f"> 参数: {args}")

            # 创建工作线程
            self.worker = Worker(args)
            self.worker.output_signal.connect(self.log_output.append)
            self.worker.error_signal.connect(self.log_output.append)
            self.worker.finished_signal.connect(self.on_function_finished)
            self.worker.start()

        except Exception as e:
            error_msg = f"[主程序异常] {str(e)}\n{traceback.format_exc()}"
            self.log_output.append(error_msg)
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def stop_function(self):
        """停止正在运行的函数"""
        if self.worker and self.worker.isRunning():
            self.log_output.append("> 正在停止...")
            self.worker.terminate()
            self.worker.wait()
            self.log_output.append("> 已停止")
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def on_function_finished(self):
        """函数执行完成"""
        self.log_output.append("> 运行结束")
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker = None

    def closeEvent(self, event):
        """窗口关闭时确保线程终止"""
        if self.worker and self.worker.isRunning():
            self.stop_function()
        event.accept()


# 工程主函数示例（放在同一工程下的main.py中）
"""
# main.py
def run(input_file=None, output_file=None):
    print("工程开始运行...")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    # 你的主要业务逻辑...
    print("工程运行完成")
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)


    # 全局异常处理
    def handle_exception(exc_type, exc_value, exc_traceback):
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        sys.stderr.write(f"未捕获的异常:\n{error_msg}")


    sys.excepthook = handle_exception

    window = PythonRunner()
    window.show()
    sys.exit(app.exec_())