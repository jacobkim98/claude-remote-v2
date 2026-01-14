# Claude Remote Control

핸드폰에서 PC의 Claude Code를 제어하는 리모컨 시스템

## 기능

1. **명령 전송**: 핸드폰에서 Claude에게 직접 명령
2. **작업 결과 보기**: Claude가 수행한 작업 내역 실시간 확인
3. **권한 요청 응답**: Allow / Deny / Always
4. **Claude 응답 보기**: Claude의 텍스트 응답을 실시간으로 확인
5. **대화 히스토리**: 사용자 메시지와 Claude 응답을 대화 형태로 표시

## 구조

```
claude-remote-v2/
├── pc/                     # PC 서버
│   ├── server.py           # 메인 서버
│   ├── window_controller.py # 창 제어 모듈
│   └── requirements.txt
│
├── hooks/                  # Claude Code Hooks
│   ├── hook_permission.py  # 권한 요청 Hook
│   ├── hook_post_tool.py   # 작업 결과 Hook
│   └── hook_stop.py        # Claude 응답 Hook (Stop Hook)
│
├── app/claude_remote/      # Flutter 앱
│   └── lib/main.dart
│
└── .claude/
    └── settings.local.json # 프로젝트 Hook 설정
```

## 설치 및 실행

### 1. PC 서버 설정

```bash
cd pc
pip install -r requirements.txt
python server.py
```

서버 시작 시 표시되는 IP 주소를 확인하세요.

### 2. Flutter 앱 빌드

```bash
cd app/claude_remote
flutter pub get
flutter build apk
```

생성된 APK를 핸드폰에 설치하세요.

### 3. 앱 연결

1. 앱에서 서버 주소 입력 (예: `192.168.0.10:8766`)
2. Connect 버튼 클릭
3. 연결 성공 시 녹색 구름 아이콘 표시

### 4. Claude Code 실행

이 프로젝트 폴더에서 Claude Code를 실행하면 Hook이 자동 적용됩니다.

```bash
cd "c:/Users/akqls/Downloads/popup claude/claude-remote-v2"
claude
```

## 사용 방법

### 명령 전송
1. 앱 하단 입력창에 명령 입력
2. 전송 버튼 클릭 (Enter 키는 비활성화됨 - 한글 입력 오류 방지)
3. PC의 Claude 창에 자동으로 입력됨

### 대화 히스토리
- **연보라색 카드**: 사용자가 보낸 메시지
- **회색 카드**: Claude 응답 (탭하면 전체 내용 보기)
- **일반 카드**: 도구 실행 결과, 권한 요청 기록

### 권한 요청 응답
- 알림으로 권한 요청이 오면 Allow/Deny/Always 선택

## 창 감지 기준

### 감지되는 창 (Class Name 기반)

| Class Name | 설명 |
|------------|------|
| `ConsoleWindowClass` | CMD (구형 명령 프롬프트) |
| `CASCADIA_HOSTING_WINDOW_CLASS` | Windows Terminal |

### 추가 감지 (제목 기반)

| 조건 | 설명 |
|------|------|
| 제목에 "claude" + "Visual Studio Code" 포함 | VSCode에서 Claude 실행 중인 창 |

### 제외되는 창

| 제외 대상 | 이유 |
|-----------|------|
| `PseudoConsoleWindow` | VSCode 내장 터미널 (ConPTY) |
| 파일 탐색기 | 제목에 "탐색기" 또는 "Explorer" 포함 시 제외 |

### 앱에서 표시되는 태그

- `[Terminal]` - CMD, PowerShell, Windows Terminal 등 터미널 창
- `[VSCode]` - VSCode에서 Claude 실행 중인 창

## 주의 사항

- PC 서버와 핸드폰이 같은 네트워크에 있어야 함
- Claude 창이 활성화되어 있어야 명령 전송 가능
- 이 프로젝트 폴더에서 실행해야 Hook이 적용됨

## 통신 구조

```
┌─────────────┐     WebSocket      ┌─────────────┐
│   Flutter   │◄──────────────────►│  PC Server  │
│     App     │     Port 8766      │  server.py  │
└─────────────┘                    └──────┬──────┘
                                          │
                                          │ HTTP POST
                                          │ Port 8765
                                          │
                                   ┌──────┴──────┐
                                   │ Claude Code │
                                   │   Hooks     │
                                   └─────────────┘
```

### 포트 정보
| 포트 | 프로토콜 | 용도 |
|------|----------|------|
| 8765 | HTTP | Hook → Server (권한 요청, 작업 결과, Claude 응답) |
| 8766 | WebSocket | App ↔ Server (실시간 양방향 통신) |

### HTTP 엔드포인트
| 경로 | 설명 |
|------|------|
| `POST /` | 권한 요청 수신 |
| `POST /tool-result` | 작업 결과 수신 |
| `POST /response` | 앱 HTTP 응답 (백그라운드) |
| `POST /claude-response` | Claude 응답 수신 (Stop Hook) |

### WebSocket 메시지 타입
| 타입 | 방향 | 설명 |
|------|------|------|
| `command` | App→Server | 명령 전송 요청 |
| `command_result` | Server→App | 명령 전송 결과 (에러 메시지 포함) |
| `permission_request` | Server→App | 권한 요청 알림 |
| `permission_response` | App→Server | 권한 응답 |
| `tool_result` | Server→App | 작업 결과 알림 |
| `claude_response` | Server→App | Claude 텍스트 응답 |
| `hwnd_update` | Server→App | 현재 연결된 창 정보 |
| `window_select` | Server→App | 창 선택 요청 (여러 개일 때) |
| `select_window` | App→Server | 창 선택 응답 |
| `refresh_windows` | App→Server | 창 목록 새로고침 요청 |
| `open_cmd` | App→Server | 새 CMD 창 열기 요청 |

## 개발 기록

### v1.0 - 초기 버전
- 기본 기능 구현 완료
  - PC 서버 (WebSocket + HTTP)
  - Flutter 앱 (리모컨 UI)
  - Claude Code Hooks (권한 요청, 작업 결과)
  - Windows 창 제어 (HWND 기반)

### v1.1 - 에러 메시지 기능 추가
- **window_controller.py**: 함수 반환값 변경
  - `activate_window()`: `bool` → `(bool, error_msg)`
  - `send_message_to_window()`: `bool` → `(bool, error_msg)`
- **server.py**: 에러 메시지를 앱으로 전송
- **main.dart**: 에러 메시지 상태바 표시 (빨간색)

### v1.2 - Claude 응답 표시 기능 추가
- **hook_stop.py**: Stop Hook 추가 - transcript에서 Claude 응답 추출
- **server.py**: `/claude-response` 엔드포인트 추가
- **main.dart**:
  - Claude 응답 카드 추가 (회색 배경, 탭하면 전체 보기)
  - 사용자 메시지 카드 추가 (연보라색 배경)
  - 대화 히스토리 형태로 표시
  - Enter 키 전송 비활성화 (한글 입력 오류 방지)
- **settings.local.json**: Stop Hook 설정 추가
- 디버그 코드 정리 및 불필요한 파일 삭제

### 시도했으나 제외된 기능
- **Notification Hook**: Claude 응답을 앱에 전송하려 했으나, Notification Hook은 시스템 메시지만 제공하고 Claude의 실제 텍스트 응답은 포함하지 않아서 제외됨
- **Stop Hook의 transcript_path**: 최종적으로 Stop Hook + transcript_path를 사용하여 Claude 응답 추출 성공

## 앞으로 개발할 목록

### 1. AskUserQuestion 알림 지원 (대기 중)
- **현재 상태**: Claude Code에서 `AskUserQuestion` Hook을 지원하지 않음
- **문제점**: Claude가 "1번 방식, 2번 방식 중 선택해주세요" 같은 질문을 할 때 앱으로 알림이 오지 않음
- **관련 GitHub Issues**:
  - [#15872](https://github.com/anthropics/claude-code/issues/15872) - AskUserQuestion Hook 지원 요청
  - [#12605](https://github.com/anthropics/claude-code/issues/12605) - AskUserQuestion Hook 지원 요청
  - [#13830](https://github.com/anthropics/claude-code/issues/13830) - 알림 Hook에 AskUserQuestion 추가 요청
- **구현 예정**: Anthropic에서 Hook 지원 시 구현
  - 앱으로 질문 내용 + 선택지 전송
  - 앱에서 선택지 버튼으로 응답
  - 선택한 답변을 Claude에게 자동 입력
