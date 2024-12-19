import pyautogui
import time
import cv2
import numpy as np
import requests
import sys
import keyboard
import threading
import os
from threading import Lock

# 用于中断程序的标志
interrupt_flag = False
interrupt_lock = Lock()

def decalibration():
    print("标定程序开始...")

    # 记录标定坐标的列表
    coordinates = []

    def get_coordinate(message):
        print(message)
        keyboard.wait('c')  # 等待用户按下"c"键
        x, y = pyautogui.position()  # 获取当前鼠标位置
        print(f"Coordinate get: ({x}, {y})")
        return (x, y)

    # 获取每个步骤的坐标
    coordinates.append(get_coordinate("请打开<激光切割>预约页面，并随机点击一个<立即下单>按钮，弹出立即下单窗口后将<鼠标悬停在勾选框处>，<按下c键>记录<坐标1>。"))
    coordinates.append(get_coordinate("鼠标悬停在<提交订单按钮>后按下c键记录坐标2。"))
    coordinates.append(get_coordinate("现在请打开要预定的运动类别网页，鼠标放置在对应运动类别上按下c键记录坐标3。"))
    coordinates.append(get_coordinate("鼠标悬停在<第一个日期>上后，按下c键记录坐标4。"))
    coordinates.append(get_coordinate("鼠标悬停在<最后一个日期>上后，按下c键记录坐标5。"))
    coordinates.append(get_coordinate("请将鼠标悬停在<拖动网页滑动条起始位置处>，按下c键获取滑动起点坐标6。"))
    coordinates.append(get_coordinate("拖动滑动条，直到<所有可预约按钮>和<立即下单按钮>全部出现在视野内。请将鼠标悬停在<拖动网页滑动条结束位置处>，按下c键获取滑动起点坐标7。"))
    coordinates.append(get_coordinate("点击第一个场地后按下c键记录坐标8。"))
    starting_time = input("请输入预约开始时间: ")
    coordinates.append(starting_time)
    coordinates.append(get_coordinate("点击最后一个场地后按下c键记录坐标9。"))
    ending_time = input("请输入预约结束时间: ")
    coordinates.append(ending_time)
    coordinates.append(get_coordinate("点击<立即下单>按钮后按下c键记录坐标10。"))

    # 保存坐标配置
    file_name = input("请输入保存坐标配置的文件名（无需后缀）：")
    conf_dir = os.path.join(os.getcwd(), "conf")
    os.makedirs(conf_dir, exist_ok=True)  # 如果不存在conf文件夹，则创建
    file_path = os.path.join(conf_dir, f"{file_name}.conf")
    with open(file_path, 'w') as f:
        for i, coord in enumerate(coordinates, start=1):
            f.write(f"Coordinate {i}: {coord}\n")
    print(f"标定完成！坐标已保存至: {file_path}")

def listen_for_interrupt():
    global interrupt_flag
    while True:
        if keyboard.is_pressed('ctrl+q'):
            with interrupt_lock:
                interrupt_flag = True
            print("检测到Ctrl+Q，程序中断。")
            break

def perform_actions(day, venue, start=None, end=None, coordinates=None):
    global interrupt_flag

    # 计算日期按钮、每一个预约按钮、截图位置的具体数值
    # 计算日期按钮date_buttons的坐标
    date_start_coor = coordinates[3];
    date_end_coor = coordinates[4];
    # 共8个日期按钮，分别计算出每个日期按钮的坐标
    date_buttons = []
    # 计算出每个日期之间的间隔，共7个间隔，用两个坐标的x坐标之差除以7
    x_interval = (date_end_coor[0] - date_start_coor[0]) / 7
    for i in range(7):
        date_buttons.append((round(date_start_coor[0] + x_interval * i), date_start_coor[1]))
    # 计算每个预约按钮的坐标
    book_buttons = []
    book_start_coor = coordinates[7]
    book_end_coor = coordinates[8]
    y_int_num = (time_end - time_start - 1)
    y_interval = (book_end_coor[1] - book_start_coor[1]) / y_int_num
    for i in range(y_int_num):
        book_buttons.append((book_start_coor[0], round(book_start_coor[1] + y_interval * i)))

    # 把date_buttons转换成day_coordinates的形式
    day_coordinates = {}
    for i, date_button in enumerate(date_buttons, start=1):
        day_coordinates[i] = date_button

    def check_interrupt():
        with interrupt_lock:
            if interrupt_flag:
                sys.exit(0)

    while True:
        check_interrupt()

        # 1. 左键单击场地对应的健身房按钮
        pyautogui.click(coordinates[2])
        time.sleep(2)

        # 2. 单击对应星期几的坐标
        pyautogui.click(*day_coordinates.get(day, (0, 0)))
        time.sleep(1)

        # 3. 执行从坐标5到坐标6的拖动操作
        mouse_drag(coordinates[5][0], coordinates[5][1], coordinates[6][0], coordinates[6][1])

        # 4. 确定截图区域
        left, top, width, height = calculate_screenshot_region(venue, book_start_coor, book_end_coor)

        # 5. 截图并保存
        screenshot_path = take_screenshot(left, top, width, height)

        # 6. 检查目标颜色
        if check_target_color(screenshot_path, left, top):
            handle_success(coordinates)
        else:
            handle_retry()

def calculate_screenshot_region(venue, book_start_coor, book_end_coor):
    # 每个按钮的尺寸是55x40
    left = book_start_coor[0] - 25
    top = book_start_coor[1] - 20
    width = book_end_coor[0] + 25 - left
    height = book_end_coor[1] + 20 - top

    return left, top, width, height

def take_screenshot(left, top, width, height):
    folder = 'screenshot'
    os.makedirs(folder, exist_ok=True)

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)

    screenshot_path = os.path.join(folder, 'latest_screenshot.png')
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    cv2.imwrite(screenshot_path, screenshot)
    return screenshot_path

def check_target_color(screenshot_path, left, top):
    screenshot = cv2.imread(screenshot_path)
    target_color = np.array([42, 191, 255])  # BGR 顺序
    mask = cv2.inRange(screenshot, target_color, target_color)

    if np.any(mask):
        color_locations = np.where(mask)
        target_y, target_x = color_locations[0][0], color_locations[1][0]
        screen_x, screen_y = target_x + left, target_y + top + 20
        pyautogui.click(screen_x, screen_y)
        return True
    return False

def handle_success(coordinates):
    pyautogui.click(coordinates[9])
    time.sleep(0.5)
    pyautogui.click(coordinates[0])
    time.sleep(0.5)
    pyautogui.click(coordinates[1])
    time.sleep(0.5)
    requests.get('http://miaotixing.com/trigger?id=tuj1K0C')
    print("程序执行完毕，退出。")
    sys.exit(0)

def handle_retry():
    print("未找到目标颜色，刷新页面并重试。")
    pyautogui.click(coordinates[5])
    pyautogui.press('f5')
    time.sleep(2)

def mouse_drag(start_x, start_y, end_x, end_y, duration=0.5):
    pyautogui.moveTo(start_x, start_y)
    time.sleep(0.1)
    pyautogui.mouseDown()
    pyautogui.moveTo(end_x, end_y, duration=duration)
    time.sleep(0.1)
    pyautogui.mouseUp()

if __name__ == "__main__":
    try:
        mode = input("请输入模式：1-标定坐标，2-执行预约：")
        if mode == "1":
            decalibration()
        elif mode == "2":
            # 读取conf文件夹中的场地名称，在页面中以序号+文件名的方式展示出来
            current_dir = os.getcwd()
            conf_folder = os.path.join(current_dir, 'conf')
            file_names = os.listdir(conf_folder)
            vfile_names = [file for file in file_names if os.path.isfile(os.path.join(conf_folder, file))]
            for idx, file in enumerate(file_names, start=1):
                print(f"{idx}. {file}")

            # 获取想要预约的场地和时间
            venue = int(input("请选择场地序号："))
            day = int(input("请问你要预约几天后的场地？（1表示今天，以此类推）："))
 
            # 根据venue的值读取对应的conf文件中的坐标
            if 1 <= venue <= len(file_names):
                selected_file = file_names[venue - 1]
                file_path = os.path.join(conf_folder, selected_file)
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                coordinates = []
                for line in lines[:8] + lines[9:10] + lines[11:12]:
                    if "Coordinate" in line:
                        coords = line.split(":")[1].strip().strip('()').split(", ")
                        coordinates.append(tuple(map(int, coords)))
                time_start = int(lines[8].split(":")[1].strip())
                time_end = int(lines[10].split(":")[1].strip())
            else:
                print("无效的序号！")

            start_input = input("请问你是否要求场地开始时间？（如果无要求，请直接敲击回车）：")
            start_time = int(start_input) if start_input else None
            end_input = input("请问你是否要求场地结束时间？（如果无要求，请直接敲击回车）：")
            end_time = int(end_input) if end_input else None

            listener_thread = threading.Thread(target=listen_for_interrupt, daemon=True)
            listener_thread.start()

            perform_actions(day, venue, start=start_time, end=end_time, coordinates=coordinates)
        else:
            print("无效模式，请重新输入1或2。")
    except Exception as e:
        print(f"程序执行出错：{e}")

