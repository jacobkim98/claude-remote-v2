#!/usr/bin/env python3
"""
Stop Hook - Claude 응답 완료 시 마지막 응답을 앱으로 전송
transcript_path에서 마지막 assistant 메시지를 추출
"""

import json
import sys
import requests

SERVER_URL = "http://localhost:8765/claude-response"


def get_last_assistant_response(transcript_path):
    """transcript 파일에서 마지막 assistant 응답 추출"""
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 역순으로 탐색해서 마지막 assistant 메시지 찾기
        for line in reversed(lines):
            try:
                msg = json.loads(line.strip())
                if msg.get('type') != 'assistant':
                    continue

                # content에서 텍스트 추출
                content = None
                if 'message' in msg and isinstance(msg['message'], dict):
                    content = msg['message'].get('content', [])
                elif 'content' in msg:
                    content = msg['content']

                if content is None:
                    continue

                text_parts = []
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get('type') == 'text':
                            text_parts.append(part.get('text', ''))
                        elif isinstance(part, str):
                            text_parts.append(part)
                elif isinstance(content, str):
                    text_parts.append(content)

                return '\n'.join(text_parts)

            except json.JSONDecodeError:
                continue
        return None
    except Exception:
        return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    transcript_path = input_data.get('transcript_path')
    session_id = input_data.get('session_id', '')

    if not transcript_path:
        sys.exit(0)

    response_text = get_last_assistant_response(transcript_path)

    if response_text:
        try:
            requests.post(SERVER_URL, json={
                "session_id": session_id,
                "response": response_text
            }, timeout=5)
        except Exception:
            pass

    sys.exit(0)


if __name__ == "__main__":
    main()
