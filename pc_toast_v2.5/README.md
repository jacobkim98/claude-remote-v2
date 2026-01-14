# Claude Code Proxy (v2)

API 프록시 방식으로 Claude Code의 tool_use를 감지하여 알림을 보내는 서버입니다.

## 특징

- **VSCode 확장에서도 동작** - Hook 버그 우회
- **CLI에서도 동작** - 동일한 방식
- API 응답에서 `tool_use` 감지 시 Windows Toast 알림

## 설치

```bash
cd claude-remote/pc_v2
pip install -r requirements.txt
```

## 사용법

### 1. 프록시 서버 실행

```bash
python proxy.py
```

### 2. Claude 설정 변경

`~/.claude/settings.json`에 추가:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:3456"
  }
}
```

### 3. Claude Code 재시작

VSCode 확장 또는 CLI를 재시작하면 프록시를 통해 API 호출이 이루어집니다.

## 동작 원리

```
Claude Code → localhost:3456 (프록시) → api.anthropic.com
                    ↓
              tool_use 감지
                    ↓
              Toast 알림!
```

## 포트 변경

`proxy.py`에서 `PROXY_PORT` 값을 수정하세요.
