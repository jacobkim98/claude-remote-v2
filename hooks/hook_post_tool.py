"""
PostToolUse Hook
- Claude가 도구 실행 완료 후 실행
- 서버에 결과 전송 → 핸드폰에서 확인 가능
"""

import sys
import json
import urllib.request
import urllib.error
import win32gui

SERVER_URL = "http://localhost:8765/tool-result"


def get_current_hwnd():
    """현재 활성 창 HWND 가져오기"""
    try:
        return win32gui.GetForegroundWindow()
    except:
        return None


def send_to_server(data):
    """서버에 HTTP POST 요청"""
    try:
        req = urllib.request.Request(
            SERVER_URL,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        # 실패해도 무시 (작업 결과 전송은 필수가 아님)
        return None


def main():
    # stdin에서 도구 실행 결과 읽기
    try:
        input_data = json.loads(sys.stdin.read())
    except:
        return

    tool_name = input_data.get("tool_name", "unknown")
    tool_input = input_data.get("tool_input", {})
    tool_result = input_data.get("tool_result", "")

    # 현재 창 HWND 가져오기
    hwnd = get_current_hwnd()

    # 서버에 결과 전송
    result_data = {
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_result": tool_result,
        "hwnd": hwnd
    }

    send_to_server(result_data)

    # PostToolUse는 응답이 필요 없음 (빈 출력)


if __name__ == "__main__":
    main()
