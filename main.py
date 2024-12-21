import sys
import os
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QComboBox, 
                            QSpinBox, QTextEdit, QMessageBox, QFileDialog,
                            QLineEdit, QInputDialog, QDialog)  # 添加缺失的导入
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import pyautogui
import cv2
import numpy as np
import requests
from threading import Lock

class BookingWorker(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, coordinates, day, venue, time_start, time_end, time_set_start, time_set_end, notify_url=None):
        super().__init__()
        self.coordinates = coordinates
        self.day = day
        self.venue = venue
        self.time_start = time_start
        self.time_end = time_end
        self.time_set_start = time_set_start
        self.time_set_end = time_set_end
        self.notify_url = notify_url
        self.interrupt_flag = False
        self.interrupt_lock = Lock()

    def run(self):
        try:
            self.perform_actions()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def perform_actions(self):
        date_start_coor = self.coordinates[3]
        date_end_coor = self.coordinates[4]
        date_buttons = []
        x_interval = (date_end_coor[0] - date_start_coor[0]) / 7
        for i in range(7):
            date_buttons.append((round(date_start_coor[0] + x_interval * i), date_start_coor[1]))

        book_buttons = []
        book_start_coor = self.coordinates[7]
        book_end_coor = self.coordinates[8]
        y_int_num = (self.time_end - self.time_start - 1)
        y_interval = (book_end_coor[1] - book_start_coor[1]) / y_int_num
        for i in range(y_int_num):
            book_buttons.append((book_start_coor[0], round(book_start_coor[1] + y_interval * i)))

        day_coordinates = {i: button for i, button in enumerate(date_buttons, start=1)}

        while not self.interrupt_flag:
            self.progress.emit(f">点击场地类别按钮，坐标: {self.coordinates[2]}")
            pyautogui.click(self.coordinates[2])
            time.sleep(2)

            selected_day_coord = day_coordinates.get(self.day, (0, 0))
            self.progress.emit(f">选择第{self.day}天，点击坐标: {selected_day_coord}")
            pyautogui.click(*selected_day_coord)
            time.sleep(1)

            self.progress.emit(f">拖动滚动条，从坐标 {self.coordinates[5]} 到 {self.coordinates[6]}")
            self.mouse_drag(self.coordinates[5][0], self.coordinates[5][1],
                            self.coordinates[6][0], self.coordinates[6][1])

            time.sleep(0.2)

            self.progress.emit(">开始截图检查可用时段...")
            screenshot_path, left_ss, top_ss = self.take_screenshot()

            if self.check_target_color(screenshot_path, left_ss, top_ss):
                self.handle_success()
                break
            else:
                self.progress.emit(">未找到可用时段，准备刷新重试")
                self.handle_retry()

    def mouse_drag(self, start_x, start_y, end_x, end_y, duration=0.5):
        pyautogui.moveTo(start_x, start_y)
        time.sleep(0.1)
        pyautogui.mouseDown()
        pyautogui.moveTo(end_x, end_y, duration=duration)
        time.sleep(0.1)
        pyautogui.mouseUp()

    def take_screenshot(self):
        folder = 'screenshot'
        os.makedirs(folder, exist_ok=True)
        
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)

        left, top, width, height = self.calculate_region()

        screenshot_path = os.path.join(folder, 'latest_screenshot.png')
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        cv2.imwrite(screenshot_path, screenshot)
        return screenshot_path,left,top
    
    def calculate_region(self):
        icon_width = round(0.768 * (self.coordinates[8][1] - self.coordinates[7][1]) / 14)
        icon_height = round(1.12 * (self.coordinates[8][1] - self.coordinates[7][1]) / 14)
        left_init = round(self.coordinates[7][0] - 0.5 * icon_width)
        top_init = round(self.coordinates[7][1] - 0.5 * icon_height)
        width_init = icon_width
        height_init = self.coordinates[8][1] - self.coordinates[7][1] + icon_height

        if self.time_set_start < self.time_start or self.time_set_end > self.time_end:
            raise ValueError("设定时间超出范围")

        left = left_init
        top = round(top_init + (self.time_set_start - self.time_start)/(self.time_end - self.time_start)*height_init)
        width = width_init
        height = round(height_init * ((self.time_set_end - self.time_set_start)/(self.time_end - self.time_start)))
        
        return left, top, width, height

    def check_target_color(self, screenshot_path, left_ss, top_ss):
        screenshot = cv2.imread(screenshot_path)
        target_color = np.array([42, 191, 255])
        mask = cv2.inRange(screenshot, target_color, target_color)

        if np.any(mask):
            color_locations = np.where(mask)
            target_y, target_x = color_locations[0][0], color_locations[1][0]
            screen_x = target_x + left_ss
            screen_y = round(target_y + top_ss + 0.5 * (self.coordinates[8][1] - self.coordinates[7][1]) / 14)

            self.progress.emit(f">找到目标颜色(42,191,255)，最左上角坐标: ({screen_x}, {screen_y})")
            self.progress.emit(f">点击预约按钮，坐标: ({screen_x}, {screen_y})")
            pyautogui.click(screen_x, screen_y)
            return True

        self.progress.emit(">未在截图中找到目标颜色(42,191,255)")
        return False

    def handle_success(self):
        self.progress.emit(f">点击立即下单按钮，坐标: {self.coordinates[9]}")
        pyautogui.click(self.coordinates[9])
        time.sleep(1)

        self.progress.emit(f">点击勾选框，坐标: {self.coordinates[0]}")
        pyautogui.click(self.coordinates[0])
        time.sleep(1)

        self.progress.emit(f">点击提交订单按钮，坐标: {self.coordinates[1]}")
        pyautogui.click(self.coordinates[1])
        time.sleep(1)

        if self.notify_url:
            try:
                requests.get(self.notify_url)
                self.progress.emit(f">发送通知到URL: {self.notify_url}")
            except:
                self.progress.emit(">通知发送失败")
        self.progress.emit(">订单提交完成！")

    def handle_retry(self):
        self.mouse_drag(self.coordinates[6][0], self.coordinates[6][1],
                        self.coordinates[5][0], self.coordinates[5][1])
        time.sleep(0.2)
        pyautogui.press('f5')
        time.sleep(5)

    def stop(self):
        with self.interrupt_lock:
            self.interrupt_flag = True

class CalibrationWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(tuple)
    url_requested = pyqtSignal()  # 新信号用于请求URL输入
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.coordinates = []
        self.current_step = 0
        self.notify_url = None
        self.steps = [
            "请打开点击任意一个可点击的<立即下单>按钮，弹出窗口后将鼠标悬停在<勾选框>处，<按下c键>记录<坐标1>",
            "鼠标悬停在<提交订单>按钮后<按下c键>记录<坐标2>",
            "现在请打开要预定的运动类别网页，鼠标悬停在对应运动类别上,<按下c键>记录<坐标3>",
            "鼠标悬停在<第一个日期>上后，<按下c键>记录<坐标4>",
            "鼠标悬停在<最后一个日期>上后，<按下c键>记录<坐标5>",
            "将鼠标悬停在<拖动网页滑动条起始位置处>，<按下c键>获取滑动起点<坐标6>",
            "拖动网页滑动条，直到<所有可预约按钮>和<立即下单按钮>全部出现在视野内，保持鼠标放置在滑动条上，<按下c键>获取滑动终点<坐标7>",
            "鼠标悬停在<第一个场地>后，<按下c键>记录<坐标8>",
            "鼠标悬停在<最后一个场地>后，<按下c键>记录<坐标9>",
            "鼠标悬停在<立即下单>按钮后，<按下c键>记录<坐标10>",
        ]

    def run(self):
        import keyboard
        
        for step in self.steps:
            if self.current_step >= len(self.steps):
                break
                
            self.progress.emit(step)
            keyboard.wait('c')
            x, y = pyautogui.position()
            self.coordinates.append((x, y))
            self.current_step += 1
            
        self.finished.emit((self.coordinates, self.notify_url))
    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.calibration_worker = None
        self.setWindowTitle("场地预约系统")
        self.setFixedSize(350, 450)
        self.setWindowFlags(
            self.windowFlags() |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.current_coordinates = None
        self.setupUI()

    def setupUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # 模式选择区域
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("选择模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["执行预约", "标定坐标"])
        self.mode_combo.currentTextChanged.connect(self.handle_mode_change)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)

        # 预约设置区域
        self.booking_widget = QWidget()
        booking_layout = QVBoxLayout(self.booking_widget)
        booking_layout.setSpacing(5)

        # 场地选择
        venue_layout = QHBoxLayout()
        venue_layout.addWidget(QLabel("场地:"))
        self.venue_combo = QComboBox()
        self.update_venue_list()
        venue_layout.addWidget(self.venue_combo)
        booking_layout.addLayout(venue_layout)

        # 日期选择
        day_layout = QHBoxLayout()
        day_layout.addWidget(QLabel("天数:"))
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 7)
        day_layout.addWidget(self.day_spin)
        booking_layout.addLayout(day_layout)

        # 时间选择
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("预约时段:"))
        self.time_start_spin = QSpinBox()
        self.time_start_spin.setRange(7, 21)
        self.time_start_spin.setValue(7)
        time_layout.addWidget(self.time_start_spin)
        time_layout.addWidget(QLabel("-"))
        self.time_end_spin = QSpinBox()
        self.time_end_spin.setRange(8, 22)
        self.time_end_spin.setValue(22)
        time_layout.addWidget(self.time_end_spin)
        booking_layout.addLayout(time_layout)

        # 执行按钮
        self.start_button = QPushButton("开始预约")
        self.start_button.clicked.connect(self.start_booking)
        booking_layout.addWidget(self.start_button)

        layout.addWidget(self.booking_widget)

        # In MainWindow.setupUI, after the start_button:
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_booking)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        booking_layout.addLayout(button_layout)

        # 标定区域
        self.calibration_widget = QWidget()
        self.calibration_widget.hide()
        calibration_layout = QVBoxLayout(self.calibration_widget)

        self.calibration_button = QPushButton("开始标定")
        self.calibration_button.clicked.connect(self.start_calibration)
        calibration_layout.addWidget(self.calibration_button)

        layout.addWidget(self.calibration_widget)

        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(200)
        self.log_text.setStyleSheet("QTextEdit { font-size: 12px; }")
        layout.addWidget(self.log_text)

        # 状态栏
        self.statusBar().setStyleSheet("QStatusBar { font-size: 11px; }")
        self.statusBar().showMessage("就绪")

        # Add URL input for booking
        notify_layout = QHBoxLayout()
        notify_layout.addWidget(QLabel("通知URL:"))
        self.notify_url_edit = QLineEdit()
        notify_layout.addWidget(self.notify_url_edit)
        booking_layout.addLayout(notify_layout)

    def stop_booking(self):
        if hasattr(self, 'booking_worker'):
            self.booking_worker.stop()
            self.log_message("正在停止预约任务...")

    def update_venue_list(self):
        self.venue_combo.clear()
        conf_folder = os.path.join(os.getcwd(), 'conf')
        if os.path.exists(conf_folder):
            files = [f for f in os.listdir(conf_folder) if f.endswith('.conf')]
            self.venue_combo.addItems([f.replace('.conf', '') for f in files])
            
        # 添加选择变更事件处理
        self.venue_combo.currentTextChanged.connect(self.on_venue_changed)

    def on_venue_changed(self, venue_name):
        if venue_name:
            conf_path = os.path.join(os.getcwd(), 'conf', f"{venue_name}.conf")
            if os.path.exists(conf_path):
                with open(conf_path, 'r') as f:
                    for line in f:
                        if "NotifyURL" in line:
                            url = line.split("NotifyURL:")[1].strip()
                            self.notify_url_edit.setText(url)
                            break

    def handle_mode_change(self, mode):
        if mode == "执行预约":
            self.booking_widget.show()
            self.calibration_widget.hide()
        else:
            self.booking_widget.hide()
            self.calibration_widget.show()

    def start_booking(self):
        venue_name = self.venue_combo.currentText()
        if not venue_name:
            QMessageBox.warning(self, "错误", "请选择场地！")
            return

        conf_path = os.path.join(os.getcwd(), 'conf', f"{venue_name}.conf")
        if not os.path.exists(conf_path):
            QMessageBox.warning(self, "错误", "找不到场地配置文件！")
            return

        with open(conf_path, 'r') as f:
            lines = f.readlines()

        coordinates = []
        notify_url = None
        for line in lines:
            if "Coordinate" in line:
                coords = line.split(":")[1].strip().strip('()').split(", ")
                coordinates.append(tuple(map(int, coords)))
            elif "NotifyURL" in line:
                notify_url = line.split("NotifyURL:")[1].strip()

        if not notify_url:
            notify_url = self.notify_url_edit.text()

        self.booking_worker = BookingWorker(
            coordinates=coordinates,
            day=self.day_spin.value(),
            venue=self.venue_combo.currentIndex() + 1,
            time_start=7,
            time_end=22,
            time_set_start=self.time_start_spin.value(),
            time_set_end=self.time_end_spin.value(),
            notify_url=notify_url
        )

        self.booking_worker.progress.connect(self.log_message)
        self.booking_worker.error.connect(self.handle_error)
        self.booking_worker.finished.connect(self.handle_booking_finished)

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.booking_worker.start()

    def start_calibration(self):
        self.calibration_worker = CalibrationWorker(self)
        self.calibration_worker.progress.connect(self.log_message)
        self.calibration_worker.finished.connect(self.handle_calibration_finished)

        # 输入URL的处理
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("输入通知URL")
        input_dialog.setLabelText("请输入通知URL（可选，留空跳过）：")
        input_dialog.setWindowFlags(input_dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        if input_dialog.exec() == QDialog.DialogCode.Accepted:
            self.calibration_worker.notify_url = input_dialog.textValue()
        else:
            self.calibration_worker.notify_url = ""

        self.calibration_button.setEnabled(False)
        self.calibration_worker.start()

    def handle_calibration_finished(self, result):
        coordinates, notify_url = result  # 正确解包tuple
        self.calibration_button.setEnabled(True)
        file_name, _ = QFileDialog.getSaveFileName(
            self, "保存配置",
            os.path.join(os.getcwd(), "conf"),
            "Configuration Files (*.conf)"
        )

        if file_name:
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            with open(file_name, 'w') as f:
                for i, coord in enumerate(coordinates, start=1):
                    f.write(f"Coordinate {i}: {coord}\n")
                if notify_url:
                    f.write(f"NotifyURL: {notify_url}\n")
            self.log_message(f"标定完成！配置已保存至: {file_name}")
            self.update_venue_list()

    def handle_booking_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_message("预约任务完成")

    def handle_error(self, error_msg):
        QMessageBox.critical(self, "错误", f"发生错误：{error_msg}")
        self.start_button.setEnabled(True)

    def log_message(self, message):
        self.log_text.append(message)
        self.statusBar().showMessage(message)

    def closeEvent(self, event):
        if hasattr(self, 'booking_worker') and self.booking_worker.isRunning():
            reply = QMessageBox.question(
                self, '确认退出',
                '预约任务正在进行中，确定要退出吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.booking_worker.stop()
                self.booking_worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()