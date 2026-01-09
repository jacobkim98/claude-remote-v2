"""
PermissionRequest Hook
- Claude가 권한 요청 시 실행
- 서버에 요청 전송 + HWND 포함
- 앱에서 응답 받아서 반환
"""

import sys
import json
import urllib.request
import urllib.error
import win32gui

SERVER_URL = "http://localhost:8765/"


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
        with urllib.request.urlopen(req, timeout=58) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"[Hook] 서버 연결 실패: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[Hook] 오류: {e}", file=sys.stderr)
        return None


def main():
    # stdin에서 권한 요청 읽기
    try:
        input_data = json.loads(sys.stdin.read())
    except:
        # 입력 파싱 실패 시 빈 응답 (기본 동작으로 fallback)
        return

    tool_name = input_data.get("tool_name", "unknown")
    tool_input = input_data.get("tool_input", {})
    session_id = input_data.get("session_id", "")

    # 현재 창 HWND 가져오기
    hwnd = get_current_hwnd()

    # 서버에 요청 전송
    request_data = {
        "request_id": f"{session_id}_{tool_name}_{id(input_data)}",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "hwnd": hwnd
    }

    response = send_to_server(request_data)

    if response:
        decision = response.get("decision", "deny")

        # Claude에게 응답 반환
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": "allowForever" if decision == "always" else decision
                }
            }
        }
        print(json.dumps(output))
    else:
        # 서버 응답 없으면 빈 출력 (기본 동작으로 fallback)
        pass


if __name__ == "__main__":
    main()
