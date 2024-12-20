import sys
import os
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QComboBox, 
                            QSpinBox, QTextEdit, QMessageBox, QFileDialog)
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
    
    def __init__(self, coordinates, day, venue, time_start, time_end):
        super().__init__()
        self.coordinates = coordinates
        self.day = day
        self.venue = venue
        self.time_start = time_start
        self.time_end = time_end
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
        # 复用原来的核心逻辑，但添加进度信息发送
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
            self.progress.emit("点击场地...")
            pyautogui.click(self.coordinates[2])
            time.sleep(2)

            self.progress.emit("选择日期...")
            pyautogui.click(*day_coordinates.get(self.day, (0, 0)))
            time.sleep(1)

            self.progress.emit("拖动滚动条...")
            self.mouse_drag(self.coordinates[5][0], self.coordinates[5][1], 
                          self.coordinates[6][0], self.coordinates[6][1])

            self.progress.emit("截图检查...")
            screenshot_path = self.take_screenshot()
            
            if self.check_target_color(screenshot_path):
                self.handle_success()
                break
            else:
                self.progress.emit("未找到可用时段，刷新重试...")
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
        
        left = self.coordinates[7][0] - 25
        top = self.coordinates[7][1] - 20
        width = self.coordinates[8][0] + 25 - left
        height = self.coordinates[8][1] + 20 - top
        
        screenshot_path = os.path.join(folder, 'latest_screenshot.png')
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        cv2.imwrite(screenshot_path, screenshot)
        return screenshot_path

    def check_target_color(self, screenshot_path):
        screenshot = cv2.imread(screenshot_path)
        target_color = np.array([42, 191, 255])
        mask = cv2.inRange(screenshot, target_color, target_color)

        if np.any(mask):
            color_locations = np.where(mask)
            target_y, target_x = color_locations[0][0], color_locations[1][0]
            left = self.coordinates[7][0] - 25
            top = self.coordinates[7][1] - 20
            screen_x, screen_y = target_x + left, target_y + top + 20
            pyautogui.click(screen_x, screen_y)
            return True
        return False

    def handle_success(self):
        self.progress.emit("预约成功，提交订单...")
        pyautogui.click(self.coordinates[9])
        time.sleep(0.5)
        pyautogui.click(self.coordinates[0])
        time.sleep(0.5)
        pyautogui.click(self.coordinates[1])
        time.sleep(0.5)
        requests.get('http://miaotixing.com/trigger?id=tuj1K0C')
        self.progress.emit("订单提交完成！")

    def handle_retry(self):
        pyautogui.click(self.coordinates[5])
        pyautogui.press('f5')
        time.sleep(2)

    def stop(self):
        with self.interrupt_lock:
            self.interrupt_flag = True

class CalibrationWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.coordinates = []
        self.current_step = 0
        self.steps = [
            "请打开<激光切割>预约页面，并随机点击一个<立即下单>按钮，弹出立即下单窗口后将<鼠标悬停在勾选框处>，<按下c键>记录<坐标1>。",
            "鼠标悬停在<提交订单按钮>后按下c键记录坐标2。",
            "现在请打开要预定的运动类别网页，鼠标放置在对应运动类别上按下c键记录坐标3。",
            "鼠标悬停在<第一个日期>上后，按下c键记录坐标4。",
            "鼠标悬停在<最后一个日期>上后，按下c键记录坐标5。",
            "请将鼠标悬停在<拖动网页滑动条起始位置处>，按下c键获取滑动起点坐标6。",
            "拖动滑动条，直到<所有可预约按钮>和<立即下单按钮>全部出现在视野内。请将鼠标悬停在<拖动网页滑动条结束位置处>，按下c键获取滑动起点坐标7。",
            "点击第一个场地后按下c键记录坐标8。",
            "点击最后一个场地后按下c键记录坐标9。",
            "点击<立即下单>按钮后按下c键记录坐标10。"
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
            
        self.finished.emit(self.coordinates)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        for line in lines:
            if "Coordinate" in line:
                coords = line.split(":")[1].strip().strip('()').split(", ")
                coordinates.append(tuple(map(int, coords)))
        
        time_start = 7
        time_end = 22

        self.booking_worker = BookingWorker(
            coordinates=coordinates,
            day=self.day_spin.value(),
            venue=self.venue_combo.currentIndex() + 1,
            time_start=time_start,
            time_end=time_end
        )
        
        self.booking_worker.progress.connect(self.log_message)
        self.booking_worker.error.connect(self.handle_error)
        self.booking_worker.finished.connect(self.handle_booking_finished)
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.booking_worker.start()

    def start_calibration(self):
        self.calibration_worker = CalibrationWorker()
        self.calibration_worker.progress.connect(self.log_message)
        self.calibration_worker.finished.connect(self.handle_calibration_finished)
        
        self.calibration_button.setEnabled(False)
        self.calibration_worker.start()
        
    def handle_calibration_finished(self, coordinates):
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