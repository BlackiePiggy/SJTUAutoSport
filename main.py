<<<<<<< HEAD
import pyautogui
import time
import cv2
import numpy as np
import requests
import sys
import argparse
import keyboard
import threading
import os

# 用于中断程序的标志
interrupt_flag = False

def listen_for_interrupt():
    global interrupt_flag
    while True:
        if keyboard.is_pressed('ctrl+q'):
            interrupt_flag = True
            print("检测到Ctrl+Q，程序中断。")
            break

def perform_actions(day, start=None, end=None):
    # 星期几对应的点击坐标
    day_coordinates = {
        1: (533, 661),  # 周一
        2: (660, 660),  # 周二
        3: (780, 660),  # 周三
        4: (910, 660),  # 周四
        5: (1020, 660), # 周五
        6: (1150, 660), # 周六
        7: (1280, 660)  # 周日
    }

    while True:
        if interrupt_flag:  # 检查中断标志
            sys.exit(0)  # 退出整个程序

        # 1. 左键单击屏幕的532,597（点击健身房按钮），等待2s
        pyautogui.click(532, 597) #点击健身房（子衿街）
        time.sleep(2)

        # 2. 左键单击对应星期几的坐标，等待1s
        pyautogui.click(*day_coordinates[day])
        time.sleep(1)

        # 执行从(1907, 224)到(1907, 387)的拖动操作
        mouse_drag(1907, 224, 1907, 387)

        # 3. 确定截图区域
        if start is not None and end is not None:
            left = 500
            top = 149 + (start - 7) * 50
            width = 561 - 500
            height = (end - start + 1) * 50
        else:
            left, top, width, height = 439, 140, 570-439, 895-140

        # 4. 截图并保存到文件夹
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 创建/清空screenshot文件夹
        folder = 'screenshot'
        if not os.path.exists(folder):
            os.makedirs(folder)
        else:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"无法删除文件 {file_path}: {e}")

        screenshot_path = os.path.join(folder, 'latest_screenshot.png')
        cv2.imwrite(screenshot_path, screenshot)

        # 5. 检查截图区域是否有RGB为（255,191,42）的颜色
        target_color = np.array([42, 191, 255])  # OpenCV使用BGR顺序
        mask = cv2.inRange(screenshot, target_color, target_color)
        
        if np.any(mask):
            print("找到目标颜色，发送公众号指令")

            # 找到目标颜色的位置
            color_locations = np.where(mask)
            target_y, target_x = color_locations[0][0], color_locations[1][0]
            
            # 转换回全屏坐标
            screen_x = target_x + left
            screen_y = target_y + top
            
            # 点击目标颜色位置
            pyautogui.click(screen_x, screen_y) # 点击有空的场次
            time.sleep(0.5)
            
            # 执行额外的点击操作
            pyautogui.click(1450, 920) # 点击立即下单按钮
            time.sleep(0.5)
            pyautogui.click(787, 760) # 点击已知同意按钮
            time.sleep(0.5)
            pyautogui.click(1060, 816) # 点击立即支付
            time.sleep(0.5)

            r = requests.get('http://miaotixing.com/trigger?id=tuj1K0C')
            print("程序执行完毕，退出。")
            sys.exit(0)  # 退出整个程序
        else:
            print("未找到目标颜色，刷新页面并重复操作")
            pyautogui.click(1700,700)
            pyautogui.press('f5')  # 刷新页面
            time.sleep(2)  # 等待页面刷新
            pyautogui.click(1909,93)
            time.sleep(0.5)  # 等待页面刷新

def mouse_drag(start_x, start_y, end_x, end_y, duration=0.5):
    # 移动鼠标到起始位置
    pyautogui.moveTo(start_x, start_y)
    
    # 短暂暂停，确保鼠标已经移动到位
    time.sleep(0.1)
    
    # 按下鼠标左键
    pyautogui.mouseDown()
    
    # 拖动到终点位置
    pyautogui.moveTo(end_x, end_y, duration=duration)
    
    # 短暂暂停，确保拖动完成
    time.sleep(0.1)
    
    # 释放鼠标左键
    pyautogui.mouseUp()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Color detection script with day selection")
    parser.add_argument("-d", type=int, choices=range(1, 8), help="Day of the week (1-7)", required=True)
    parser.add_argument("-s", "--start", type=int, help="Start time (optional)")
    parser.add_argument("-e", "--end", type=int, help="End time (optional)")
    args = parser.parse_args()

    print(f"程序将在3秒后开始运行，将执行星期{args.d}的操作。请将鼠标移开...")
    time.sleep(3)

    # 启动键盘监听线程
    listener_thread = threading.Thread(target=listen_for_interrupt, daemon=True)
    listener_thread.start()

    perform_actions(args.d, start=args.start, end=args.end)
=======
import pyautogui
import time
import cv2
import numpy as np
import requests
import sys
import keyboard
import threading
import os

# 用于中断程序的标志
interrupt_flag = False

def listen_for_interrupt():
    global interrupt_flag
    while True:
        if keyboard.is_pressed('ctrl+q'):
            interrupt_flag = True
            print("检测到Ctrl+Q，程序中断。")
            break

def perform_actions(day, start=None, end=None):
    # 星期几对应的点击坐标
    day_coordinates = {
        1: (533, 661),  # 周一
        2: (660, 660),  # 周二
        3: (780, 660),  # 周三
        4: (910, 660),  # 周四
        5: (1020, 660), # 周五
        6: (1150, 660), # 周六
        7: (1280, 660)  # 周日
    }

    while True:
        if interrupt_flag:  # 检查中断标志
            sys.exit(0)  # 退出整个程序

        # 1. 左键单击屏幕的532,597（点击健身房按钮），等待2s
        pyautogui.click(532, 597) #点击健身房（子衿街）
        time.sleep(2)

        # 2. 左键单击对应星期几的坐标，等待1s
        pyautogui.click(*day_coordinates[day])
        time.sleep(1)

        # 执行从(1907, 224)到(1907, 387)的拖动操作
        mouse_drag(1907, 224, 1907, 387)

        # 3. 确定截图区域
        if start is not None and end is not None:
            left = 500
            top = 149 + (start - 7) * 50
            width = 561 - 500
            height = (end - start + 1) * 50
        else:
            left, top, width, height = 439, 140, 570-439, 895-140

        # 4. 截图并保存到文件夹
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 创建/清空screenshot文件夹
        folder = 'screenshot'
        if not os.path.exists(folder):
            os.makedirs(folder)
        else:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"无法删除文件 {file_path}: {e}")

        screenshot_path = os.path.join(folder, 'latest_screenshot.png')
        cv2.imwrite(screenshot_path, screenshot)

        # 5. 检查截图区域是否有RGB为（255,191,42）的颜色
        target_color = np.array([42, 191, 255])  # OpenCV使用BGR顺序
        mask = cv2.inRange(screenshot, target_color, target_color)
        
        if np.any(mask):
            print("找到目标颜色，发送公众号指令")

            # 找到目标颜色的位置
            color_locations = np.where(mask)
            target_y, target_x = color_locations[0][0], color_locations[1][0]
            
            # 转换回全屏坐标
            screen_x = target_x + left
            screen_y = target_y + top
            
            # 点击目标颜色位置
            pyautogui.click(screen_x, screen_y) # 点击有空的场次
            time.sleep(0.5)
            
            # 执行额外的点击操作
            pyautogui.click(1450, 920) # 点击立即下单按钮
            time.sleep(0.5)
            pyautogui.click(787, 760) # 点击已知同意按钮
            time.sleep(0.5)
            pyautogui.click(1060, 816) # 点击立即支付
            time.sleep(0.5)

            r = requests.get('http://miaotixing.com/trigger?id=tuj1K0C')
            print("程序执行完毕，退出。")
            sys.exit(0)  # 退出整个程序
        else:
            print("未找到目标颜色，刷新页面并重复操作")
            pyautogui.click(1700,700)
            pyautogui.press('f5')  # 刷新页面
            time.sleep(2)  # 等待页面刷新
            pyautogui.click(1909,93)
            time.sleep(0.5)  # 等待页面刷新

def mouse_drag(start_x, start_y, end_x, end_y, duration=0.5):
    # 移动鼠标到起始位置
    pyautogui.moveTo(start_x, start_y)
    
    # 短暂暂停，确保鼠标已经移动到位
    time.sleep(0.1)
    
    # 按下鼠标左键
    pyautogui.mouseDown()
    
    # 拖动到终点位置
    pyautogui.moveTo(end_x, end_y, duration=duration)
    
    # 短暂暂停，确保拖动完成
    time.sleep(0.1)
    
    # 释放鼠标左键
    pyautogui.mouseUp()

if __name__ == "__main__":
    # 获取用户输入
    day = int(input("请问你要预约几天后的场地？（1表示今天，以此类推）："))
    
    # 开始时间输入，用户如果没有输入则设为None
    start_input = input("请问你是否要求场地开始时间？（如果无要求，请直接敲击回车）：")
    if start_input:
        start_time = int(start_input)
        # 如果有开始时间，再询问结束时间
        end_input = input("请问你是否要求场地结束时间？（如果无要求，请直接敲击回车）：")
        if end_input:
            end_time = int(end_input)
        else:
            end_time = None
    else:
        start_time = None
        end_time = None

    print(f"程序将在3秒后开始运行，将执行{day}天后的场地预订操作。请将鼠标移开...")
    time.sleep(3)

    # 启动键盘监听线程
    listener_thread = threading.Thread(target=listen_for_interrupt, daemon=True)
    listener_thread.start()

    # 执行操作
    perform_actions(day, start=start_time, end=end_time)
>>>>>>> 271a9c0 (change args input way)
