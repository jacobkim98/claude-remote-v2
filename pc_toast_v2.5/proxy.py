#!/usr/bin/env python3
"""
Claude Code Proxy Server
- API 요청을 api.anthropic.com으로 프록시
- 응답에서 tool_use 감지 시 Toast 알림
"""

import json
import asyncio
import aiohttp
from aiohttp import web
import threading
import time

# Windows Toast
try:
    from windows_toasts import InteractableWindowsToaster, Toast, ToastButton, ToastActivatedEventArgs
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False
    print("[WARNING] windows_toasts not installed. Toast notifications disabled.")

# Window control
try:
    import pyautogui
    import pygetwindow as gw
    WINDOW_CONTROL_AVAILABLE = True
except ImportError:
    WINDOW_CONTROL_AVAILABLE = False
    print("[WARNING] pyautogui/pygetwindow not installed. Window control disabled.")

# 설정
ANTHROPIC_API_URL = "https://api.anthropic.com"
PROXY_PORT = 3456


def send_key_to_vscode(key: str):
    """VSCode 창에 키 입력 전송"""
    if not WINDOW_CONTROL_AVAILABLE:
        print(f"[KEY] Window control not available")
        return False

    try:
        # VSCode 창 찾기
        vscode_windows = [w for w in gw.getWindowsWithTitle('Visual Studio Code') if w.visible]
        if not vscode_windows:
            print("[KEY] VSCode window not found")
            return False

        # 첫 번째 VSCode 창 활성화
        vscode_win = vscode_windows[0]
        vscode_win.activate()
        time.sleep(0.3)  # 창 활성화 대기

        # 키 입력
        pyautogui.press(key)
        print(f"[KEY] Sent key '{key}' to VSCode")
        return True
    except Exception as e:
        print(f"[KEY ERROR] {e}")
        return False


def on_toast_activated(args: ToastActivatedEventArgs):
    """Toast 버튼 클릭 핸들러"""
    action = args.arguments
    print(f"[TOAST] Button clicked: {action}")

    if action == "allow":
        # VSCode로 가서 '1' (Yes) 누르기
        send_key_to_vscode('1')
    elif action == "deny":
        # VSCode로 가서 '3' (No) 누르기
        send_key_to_vscode('3')


def show_toast(tool_name: str, tool_input: dict):
    """Windows Toast 알림 표시 (버튼 포함)"""
    if not TOAST_AVAILABLE:
        print(f"[TOOL_USE] {tool_name}: {tool_input}")
        return

    # VSCode permission 다이얼로그가 뜰 때까지 대기
    time.sleep(1.2)

    try:
        # 알림 내용 구성
        body = tool_name
        if isinstance(tool_input, dict):
            if "command" in tool_input:
                body = f"Bash: {tool_input['command'][:100]}"
            elif "file_path" in tool_input:
                body = f"{tool_name}: {tool_input['file_path']}"

        if len(body) > 150:
            body = body[:147] + "..."

        toaster = InteractableWindowsToaster("Claude Code Proxy")
        toast = Toast()
        toast.text_fields = ["Tool Use Detected", body]

        # 버튼 추가
        toast.AddAction(ToastButton("Allow", "allow"))
        toast.AddAction(ToastButton("Deny", "deny"))

        # 버튼 클릭 핸들러 등록
        toast.on_activated = on_toast_activated

        toaster.show_toast(toast)
    except Exception as e:
        print(f"[TOAST ERROR] {e}")


def detect_tool_use(response_data: dict):
    """응답에서 tool_use 감지"""
    content = response_data.get("content", [])

    for item in content:
        if isinstance(item, dict) and item.get("type") == "tool_use":
            tool_name = item.get("name", "unknown")
            tool_input = item.get("input", {})

            # 별도 스레드에서 Toast 표시 (블로킹 방지)
            threading.Thread(
                target=show_toast,
                args=(tool_name, tool_input),
                daemon=True
            ).start()


async def proxy_handler(request: web.Request):
    """API 요청 프록시 핸들러"""
    # 원본 경로 구성
    path = request.path
    target_url = f"{ANTHROPIC_API_URL}{path}"

    # 요청 헤더 복사 (host 제외)
    headers = {
        key: value for key, value in request.headers.items()
        if key.lower() not in ('host', 'content-length')
    }

    # 요청 본문 읽기
    body = await request.read()

    print(f"[PROXY] {request.method} {path}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=body,
                ssl=True
            ) as resp:
                # 응답 본문 읽기
                response_body = await resp.read()

                # Content-Type 확인
                content_type = resp.headers.get('Content-Type', '')
                print(f"[DEBUG] Content-Type: {content_type}")

                # JSON 응답이면 tool_use 감지
                if 'application/json' in content_type:
                    try:
                        response_data = json.loads(response_body)
                        print(f"[DEBUG] JSON response, checking for tool_use...")
                        detect_tool_use(response_data)
                    except json.JSONDecodeError:
                        pass
                # Streaming 응답 처리 (text/event-stream)
                elif 'text/event-stream' in content_type:
                    print(f"[DEBUG] Streaming response detected")
                    # streaming 데이터에서 tool_use 이벤트 찾기
                    try:
                        text = response_body.decode('utf-8')
                        for line in text.split('\n'):
                            if line.startswith('data: '):
                                data_str = line[6:]  # 'data: ' 제거
                                if data_str.strip() == '[DONE]':
                                    continue
                                try:
                                    event_data = json.loads(data_str)
                                    # content_block_start 이벤트에서 tool_use 감지
                                    if event_data.get('type') == 'content_block_start':
                                        content_block = event_data.get('content_block', {})
                                        if content_block.get('type') == 'tool_use':
                                            tool_name = content_block.get('name', 'unknown')
                                            print(f"[DEBUG] Found tool_use in stream: {tool_name}")
                                            threading.Thread(
                                                target=show_toast,
                                                args=(tool_name, {}),
                                                daemon=True
                                            ).start()
                                except json.JSONDecodeError:
                                    pass
                    except Exception as e:
                        print(f"[DEBUG] Stream parse error: {e}")

                # 응답 헤더 복사
                response_headers = {
                    key: value for key, value in resp.headers.items()
                    if key.lower() not in ('content-encoding', 'transfer-encoding', 'content-length')
                }

                return web.Response(
                    status=resp.status,
                    headers=response_headers,
                    body=response_body
                )
        except Exception as e:
            print(f"[ERROR] Proxy error: {e}")
            return web.Response(status=502, text=f"Proxy error: {e}")


async def health_check(request: web.Request):
    """헬스 체크 엔드포인트"""
    return web.json_response({"status": "ok", "service": "claude-code-proxy"})


def main():
    print(f"""
========================================================
          Claude Code Proxy Server
========================================================
  Listening on: http://localhost:{PROXY_PORT}
  Proxying to:  {ANTHROPIC_API_URL}
  Toast notifications: {'Enabled' if TOAST_AVAILABLE else 'Disabled'}
========================================================

Add to ~/.claude/settings.json:
{{
  "env": {{
    "ANTHROPIC_BASE_URL": "http://localhost:{PROXY_PORT}"
  }}
}}
""")

    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_route('*', '/{path:.*}', proxy_handler)

    web.run_app(app, host='127.0.0.1', port=PROXY_PORT, print=None)


if __name__ == "__main__":
    main()
