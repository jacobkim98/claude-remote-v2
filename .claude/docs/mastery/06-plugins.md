# 6. Plugins (플러그인)

> 이 문서는 [CLAUDE-CODE-MASTERY.md](../CLAUDE-CODE-MASTERY.md)의 일부입니다.

---

## 6.1 플러그인이란?

**플러그인**은 Claude Code의 기능을 확장하는 재사용 가능한 패키지입니다. Commands, Agents, Skills를 하나의 번들로 묶어 다른 프로젝트나 팀에 배포할 수 있습니다.

**플러그인 vs 로컬 설정**:

| 구분 | 로컬 설정 | 플러그인 |
|------|----------|----------|
| 위치 | `.claude/` 폴더 | Marketplace 또는 URL |
| 범위 | 해당 프로젝트 | 여러 프로젝트 공유 |
| 배포 | Git | Marketplace/HTTP |
| 업데이트 | 수동 | 자동 |

---

## 6.2 플러그인 구조

```
my-plugin/
├── plugin.json              # 플러그인 매니페스트 (필수)
├── README.md                # 설명 문서
├── commands/                # 슬래시 커맨드
│   └── my-command.md
├── agents/                  # 서브 에이전트
│   └── my-agent.md
├── skills/                  # 스킬
│   └── my-skill/
│       └── SKILL.md
└── hooks/                   # 훅 스크립트
    └── format.sh
```

---

## 6.3 plugin.json (매니페스트)

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "플러그인 설명",
  "author": "작성자",
  "homepage": "https://github.com/...",
  "license": "MIT",
  "claude": {
    "minVersion": "1.0.0"
  },
  "commands": ["commands/my-command.md"],
  "agents": ["agents/my-agent.md"],
  "skills": ["skills/my-skill"],
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "script": "hooks/format.sh"
    }]
  },
  "permissions": {
    "allow": ["Bash(npm:*)"],
    "deny": []
  }
}
```

**필수 필드**:

| 필드 | 설명 |
|------|------|
| `name` | 플러그인 고유 이름 (kebab-case) |
| `version` | Semantic Versioning (1.0.0) |
| `description` | 간단한 설명 (최대 200자) |

**선택 필드**:

| 필드 | 설명 |
|------|------|
| `author` | 작성자/조직 |
| `homepage` | GitHub/웹사이트 URL |
| `license` | 라이선스 (MIT, Apache-2.0 등) |
| `claude.minVersion` | 최소 Claude Code 버전 |
| `commands` | 포함할 커맨드 목록 |
| `agents` | 포함할 에이전트 목록 |
| `skills` | 포함할 스킬 폴더 목록 |
| `hooks` | 훅 정의 |
| `permissions` | 권한 설정 |

---

## 6.4 플러그인 설치

```bash
# Marketplace에서 설치
claude plugin install @org/plugin-name

# URL에서 설치
claude plugin install https://github.com/org/plugin/releases/latest/download/plugin.zip

# 로컬 경로에서 설치
claude plugin install ./path/to/plugin
```

**설치된 플러그인 관리**:

```bash
# 목록 확인
claude plugin list

# 업데이트
claude plugin update @org/plugin-name

# 제거
claude plugin remove @org/plugin-name
```

---

## 6.5 플러그인 개발

**1단계: 플러그인 초기화**

```bash
mkdir my-plugin && cd my-plugin
claude plugin init
```

**2단계: 기능 추가**

```bash
# 커맨드 추가
mkdir commands
cat > commands/my-command.md << 'EOF'
# My Command

이 커맨드는...

## 수행 작업
1. ...
2. ...
EOF
```

**3단계: 로컬 테스트**

```bash
# 현재 프로젝트에서 테스트
claude plugin link .

# 테스트
/my-command

# 링크 해제
claude plugin unlink my-plugin
```

**4단계: 배포**

```bash
# 패키징
claude plugin pack

# Marketplace 배포
claude plugin publish

# 또는 GitHub Release로 배포
```

---

## 6.6 Prebuilt Plugins (마켓플레이스)

**공식 플러그인 예시**:

| 플러그인 | 설명 |
|----------|------|
| `@anthropic/git-workflow` | Git 워크플로우 자동화 |
| `@anthropic/code-review` | 코드 리뷰 에이전트 |
| `@anthropic/testing` | 테스트 작성/실행 도구 |
| `@anthropic/docs` | 문서 생성 도구 |

**검색 및 설치**:

```bash
# Marketplace 검색
claude plugin search "testing"

# 인기 플러그인 보기
claude plugin browse --sort=downloads

# 설치
claude plugin install @anthropic/testing
```