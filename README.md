# Claude Remote Control

핸드폰에서 PC의 Claude Code를 제어하는 리모컨 시스템

## 기능

1. **명령 전송**: 핸드폰에서 Claude에게 직접 명령
2. **작업 결과 보기**: Claude가 수행한 작업 내역 실시간 확인
3. **권한 요청 응답**: Allow / Deny / Always

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
│   └── hook_post_tool.py   # 작업 결과 Hook
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
2. 전송 버튼 클릭
3. PC의 Claude 창에 자동으로 입력됨

### 작업 결과 보기
- Claude가 도구를 실행할 때마다 앱에 실시간으로 표시됨

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
