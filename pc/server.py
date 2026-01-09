"""
Claude Remote Control Server
- WebSocket: 핸드폰 앱과 실시간 통신
- HTTP: Hook에서 데이터 수신
- 창 제어: Claude 창에 메시지 전송
"""

import asyncio
import json
import websockets
from aiohttp import web
import time
import socket
import subprocess
from window_controller import (
    send_message_to_window, is_window_valid, get_window_title,
    find_windows_by_title, find_windows_by_class, TERMINAL_CLASSES, VSCODE_CLASS
)


def get_local_ip():
    """로컬 IP 주소 가져오기"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


# 연결된 앱 클라이언트
connected_app = None

# 현재 Claude 창 HWND
current_hwnd = None

# 권한 요청 대기열
pending_requests = {}

# 작업 히스토리 (최근 100개)
tool_history = []
MAX_HISTORY = 100


class PermissionRequest:
    def __init__(self, request_id, tool_name, tool_input):
        self.request_id = request_id
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.response = None
        self.event = asyncio.Event()


async def broadcast_to_app(message):
    """앱에 메시지 전송"""
    global connected_app
    if connected_app:
        try:
            await connected_app.send(json.dumps(message))
            return True
        except:
            return False
    return False


async def detect_claude_windows():
    """Claude 창 감지 및 앱에 알림"""
    global current_hwnd

    loop = asyncio.get_event_loop()

    # 1. Class Name으로 터미널 창 찾기
    terminal_windows = await loop.run_in_executor(None, find_windows_by_class, TERMINAL_CLASSES)

    # 2. 제목에 'claude' 포함된 창 찾기 (VSCode 등)
    claude_title_windows = await loop.run_in_executor(None, find_windows_by_title, "claude")

    # 3. VSCode에서 Claude 실행 중인 창 찾기
    vscode_claude = [w for w in claude_title_windows
                     if w.get('class_name') == VSCODE_CLASS and 'Visual Studio Code' in w['title']]

    # 중복 제거 (hwnd 기준)
    seen = set()
    all_windows = []

    # 터미널 창 추가
    for w in terminal_windows:
        if w['hwnd'] not in seen:
            seen.add(w['hwnd'])
            # 제목이 없으면 "Terminal" 표시
            if not w['title']:
                w['title'] = "[Terminal] (No Title)"
            else:
                w['title'] = f"[Terminal] {w['title']}"
            all_windows.append(w)

    # VSCode Claude 창 추가
    for w in vscode_claude:
        if w['hwnd'] not in seen:
            seen.add(w['hwnd'])
            w['title'] = f"[VSCode] {w['title']}"
            all_windows.append(w)

    if not all_windows:
        print("[서버] Claude 창 없음")
        return

    if len(all_windows) == 1:
        # 창이 하나면 자동 연결
        current_hwnd = all_windows[0]['hwnd']
        print(f"[서버] Claude 창 자동 연결: {all_windows[0]['title']}")
        await broadcast_to_app({
            "type": "hwnd_update",
            "hwnd": current_hwnd,
            "title": all_windows[0]['title']
        })
    else:
        # 여러 개면 앱에 선택 요청
        print(f"[서버] Claude 창 {len(all_windows)}개 발견 - 선택 요청")
        await broadcast_to_app({
            "type": "window_select",
            "windows": all_windows
        })


async def handle_app_connection(websocket):
    """앱 WebSocket 연결 처리"""
    global connected_app, current_hwnd
    connected_app = websocket
    print("[서버] 앱 연결됨")

    # 연결 시 Claude 창 감지
    await detect_claude_windows()

    # 현재 HWND가 있으면 전송
    if current_hwnd and is_window_valid(current_hwnd):
        await websocket.send(json.dumps({
            "type": "hwnd_update",
            "hwnd": current_hwnd,
            "title": get_window_title(current_hwnd)
        }))

    # 최근 히스토리 전송
    if tool_history:
        await websocket.send(json.dumps({
            "type": "history_sync",
            "history": tool_history[-20:]  # 최근 20개
        }))

    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"[서버] 앱에서 수신: {data.get('type')}")

            if data.get('type') == 'command':
                # 핸드폰에서 명령 수신 → Claude 창에 전송
                hwnd = data.get('hwnd') or current_hwnd
                msg = data.get('message', '')

                if hwnd and msg:
                    # 비동기로 창 제어 실행 (블로킹 방지)
                    loop = asyncio.get_event_loop()
                    success, error_msg = await loop.run_in_executor(
                        None, send_message_to_window, hwnd, msg
                    )
                    result = {
                        "type": "command_result",
                        "success": success,
                        "message": msg[:50]
                    }
                    if error_msg:
                        result["error"] = error_msg
                    await websocket.send(json.dumps(result))
                else:
                    await websocket.send(json.dumps({
                        "type": "command_result",
                        "success": False,
                        "error": "HWND or message missing"
                    }))

            elif data.get('type') == 'permission_response':
                # 권한 응답
                request_id = data.get("request_id")
                if request_id and request_id in pending_requests:
                    req = pending_requests[request_id]
                    req.response = data.get("decision", "deny")
                    req.event.set()

            elif data.get('type') == 'select_window':
                # 앱에서 창 선택
                hwnd = data.get('hwnd')
                if hwnd and is_window_valid(hwnd):
                    current_hwnd = hwnd
                    title = get_window_title(hwnd)
                    print(f"[서버] 창 선택됨: {title}")
                    await websocket.send(json.dumps({
                        "type": "hwnd_update",
                        "hwnd": current_hwnd,
                        "title": title
                    }))

            elif data.get('type') == 'refresh_windows':
                # 앱에서 창 새로고침 요청
                await detect_claude_windows()

            elif data.get('type') == 'ping':
                await websocket.send(json.dumps({"type": "pong"}))

            elif data.get('type') == 'open_cmd':
                # 새 CMD 창 열기
                try:
                    subprocess.Popen('start cmd', shell=True)
                    print("[서버] CMD 창 열기 요청")
                    await websocket.send(json.dumps({
                        "type": "cmd_result",
                        "success": True
                    }))
                    # 잠시 후 창 목록 새로고침
                    await asyncio.sleep(0.5)
                    await detect_claude_windows()
                except Exception as e:
                    print(f"[서버] CMD 열기 실패: {e}")
                    await websocket.send(json.dumps({
                        "type": "cmd_result",
                        "success": False,
                        "error": str(e)
                    }))

    except websockets.exceptions.ConnectionClosed:
        print("[서버] 앱 연결 끊김")
    finally:
        connected_app = None


async def handle_permission_request(request):
    """Hook에서 권한 요청 수신"""
    global current_hwnd

    data = await request.json()
    tool_name = data.get("tool_name", "unknown")
    tool_input = data.get("tool_input", {})
    request_id = data.get("request_id", str(time.time()))
    hwnd = data.get("hwnd")

    # HWND 업데이트
    if hwnd:
        current_hwnd = hwnd
        await broadcast_to_app({
            "type": "hwnd_update",
            "hwnd": hwnd,
            "title": get_window_title(hwnd) if is_window_valid(hwnd) else ""
        })

    print(f"[서버] 권한 요청: {tool_name}")

    # 앱이 연결되어 있지 않으면 Hook 무시 (Claude Code 기본 동작)
    if connected_app is None:
        print("[서버] 앱 미연결 - PC에서 처리")
        return web.json_response({"decision": ""})

    # 대기열에 추가
    req = PermissionRequest(request_id, tool_name, tool_input)
    pending_requests[request_id] = req

    # 앱에 알림 전송
    await broadcast_to_app({
        "type": "permission_request",
        "request_id": request_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "hwnd": current_hwnd
    })

    # 응답 대기
    try:
        await asyncio.wait_for(req.event.wait(), timeout=55)
        decision = req.response
    except asyncio.TimeoutError:
        decision = "deny"

    # 대기열에서 제거
    if request_id in pending_requests:
        del pending_requests[request_id]

    print(f"[서버] 권한 응답: {decision}")
    return web.json_response({"decision": decision})


async def handle_tool_result(request):
    """Hook에서 작업 결과 수신"""
    global current_hwnd

    data = await request.json()
    tool_name = data.get("tool_name", "unknown")
    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", "")
    hwnd = data.get("hwnd")

    # HWND 업데이트
    if hwnd:
        current_hwnd = hwnd

    # 히스토리에 저장
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tool_name": tool_name,
        "tool_input": tool_input,
        "result_summary": str(tool_result)[:200],  # 요약
        "hwnd": current_hwnd
    }
    tool_history.append(entry)
    if len(tool_history) > MAX_HISTORY:
        tool_history.pop(0)

    print(f"[서버] 작업 결과: {tool_name}")

    # 앱에 전송
    await broadcast_to_app({
        "type": "tool_result",
        **entry
    })

    return web.json_response({"status": "ok"})


async def handle_app_http_response(request):
    """앱 백그라운드에서 HTTP로 권한 응답 받기"""
    data = await request.json()
    print(f"[서버] 앱 HTTP 응답: {data}")

    request_id = data.get("request_id")
    decision = data.get("decision", "deny")

    if request_id and request_id in pending_requests:
        req = pending_requests[request_id]
        req.response = decision
        req.event.set()
        return web.json_response({"status": "ok"})

    return web.json_response({"status": "not_found"}, status=404)


async def main():
    # HTTP 서버 설정
    app = web.Application()
    app.router.add_post('/', handle_permission_request)  # 권한 요청
    app.router.add_post('/tool-result', handle_tool_result)  # 작업 결과
    app.router.add_post('/response', handle_app_http_response)  # 앱 HTTP 응답

    runner = web.AppRunner(app)
    await runner.setup()
    http_site = web.TCPSite(runner, '0.0.0.0', 8765)
    await http_site.start()
    print("[서버] HTTP 서버 시작: 0.0.0.0:8765")

    # WebSocket 서버 시작
    print("[서버] WebSocket 서버 시작: 0.0.0.0:8766")
    async with websockets.serve(handle_app_connection, "0.0.0.0", 8766):
        await asyncio.Future()  # 무한 대기


if __name__ == "__main__":
    local_ip = get_local_ip()
    print("=" * 50)
    print("  Claude Remote Control Server")
    print("=" * 50)
    print(f"  앱에서 연결할 주소: {local_ip}:8766")
    print("=" * 50)
    print()
    asyncio.run(main())
