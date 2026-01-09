"""
Windows 창 제어 모듈
- HWND로 창 찾기 및 활성화
- 클립보드 + 붙여넣기로 메시지 입력
"""

import win32gui
import win32con
import pyautogui
import pyperclip
import time


def get_foreground_hwnd():
    """현재 활성 창의 HWND 반환"""
    return win32gui.GetForegroundWindow()


def get_window_title(hwnd):
    """HWND로 창 제목 가져오기"""
    try:
        return win32gui.GetWindowText(hwnd)
    except:
        return ""


def is_window_valid(hwnd):
    """HWND가 유효한 창인지 확인"""
    try:
        return win32gui.IsWindow(hwnd)
    except:
        return False


def activate_window(hwnd):
    """HWND로 창 활성화"""
    try:
        # 창이 최소화되어 있으면 복원
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        # 창 활성화
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.1)  # 활성화 대기
        return True
    except Exception as e:
        print(f"[창 제어] 활성화 실패: {e}")
        return False


def send_message_to_window(hwnd, message):
    """
    특정 창에 메시지 전송
    1. 창 활성화
    2. 클립보드에 복사
    3. Ctrl+V 붙여넣기
    4. Enter 전송
    """
    try:
        # 창 유효성 확인
        if not is_window_valid(hwnd):
            print(f"[창 제어] 유효하지 않은 HWND: {hwnd}")
            return False

        # 창 활성화
        if not activate_window(hwnd):
            return False

        # 클립보드에 메시지 복사
        pyperclip.copy(message)
        time.sleep(0.05)

        # Ctrl+V 붙여넣기
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)

        # Enter 전송
        pyautogui.press('enter')

        print(f"[창 제어] 메시지 전송 완료: {message[:50]}...")
        return True

    except Exception as e:
        print(f"[창 제어] 메시지 전송 실패: {e}")
        return False


def find_windows_by_title(keyword):
    """제목에 특정 키워드가 포함된 모든 창 찾기"""
    results = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if keyword.lower() in title.lower():
                results.append({
                    'hwnd': hwnd,
                    'title': title,
                    'class_name': win32gui.GetClassName(hwnd)
                })
        return True

    win32gui.EnumWindows(callback, None)
    return results


def find_windows_by_class(class_names):
    """Class Name으로 창 찾기 (터미널 창 감지용)"""
    results = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            class_name = win32gui.GetClassName(hwnd)
            if class_name in class_names:
                title = win32gui.GetWindowText(hwnd)
                results.append({
                    'hwnd': hwnd,
                    'title': title,
                    'class_name': class_name
                })
        return True

    win32gui.EnumWindows(callback, None)
    return results


# 터미널 관련 Class Names
TERMINAL_CLASSES = [
    'ConsoleWindowClass',           # CMD (구형)
    'CASCADIA_HOSTING_WINDOW_CLASS', # Windows Terminal
    # 'PseudoConsoleWindow' 제외 - VSCode 내장 터미널에서 사용됨
]

VSCODE_CLASS = 'Chrome_WidgetWin_1'


if __name__ == "__main__":
    # 테스트
    print("현재 활성 창 HWND:", get_foreground_hwnd())

    print("\n=== 터미널 창 (Class Name 기반) ===")
    for w in find_windows_by_class(TERMINAL_CLASSES):
        print(f"  HWND: {w['hwnd']}, Class: {w['class_name']}, Title: {w['title']}")

    print("\n=== 'claude' 포함된 창 ===")
    for w in find_windows_by_title("claude"):
        print(f"  HWND: {w['hwnd']}, Class: {w['class_name']}, Title: {w['title']}")
