# 4. 교육 커리큘럼

> 이 문서는 [CLAUDE-CODE-MASTERY.md](../CLAUDE-CODE-MASTERY.md)의 일부입니다.

---

## 4.0 레벨 판단 기준

### 판단 기준표

| 레벨 | 조건 | 학습 내용 |
|------|------|----------|
| 1 | CLAUDE.md 없음 | 기초: CLAUDE.md 작성법, Plan Mode |
| 2 | CLAUDE.md만 있음 | 자동화: Commands, Hooks, 권한 관리 |
| 3 | Commands/Hooks 있음 | 전문화: Agents, Skills, MCP |
| 4 | 대부분 설정 완료 | 팀 최적화: GitHub Action, 팀 규칙 |

### 기본 제공 파일 제외 (중요!)

다음 파일/폴더는 **학습 시스템의 기본 제공 파일**이므로 레벨 판단 시 **제외**해야 합니다:

```bash
# 제외할 파일/폴더 (사용자 설정으로 카운트하지 않음)
- .claude/commands/learn-claude-code.md      # 학습 커맨드
- .claude/commands/setup-claude-code.md      # 설정 생성 커맨드
- .claude/commands/upgrade-claude-code.md    # 업그레이드 커맨드
- .claude/docs/                              # 마스터 가이드 문서 전체
```

**예시**:
- `.claude/commands/`에 위 3개 파일만 있으면 → "Commands 없음"으로 판단
- `.claude/commands/commit.md`가 추가로 있으면 → "Commands 있음"으로 판단

---

## 4.1 레벨 1: 기초 (15분)

**대상**: Claude Code 처음 사용자

**학습 내용**:
1. CLAUDE.md의 목적과 작성법
2. 기본 명령어 사용
3. Plan Mode 활용

**실습**:
```bash
# CLAUDE.md 생성
# 첫 번째 규칙 추가해보기
```

---

## 4.2 레벨 2: 자동화 (30분)

**대상**: 기초 완료 사용자

**학습 내용**:
1. 슬래시 커맨드 생성
2. PostToolUse 훅 설정
3. 권한 관리

**실습**:
```bash
# /commit-push-pr 커맨드 생성
# 포맷팅 훅 설정
```

---

## 4.3 레벨 3: 전문화 (45분)

**대상**: 자동화 완료 사용자

**학습 내용**:
1. 서브 에이전트 생성
2. Skills 정의
3. MCP 통합

**실습**:
```bash
# build-validator 에이전트 생성
# 도메인별 skill 생성
```

---

## 4.4 레벨 4: 팀 최적화 (1시간)

**대상**: 팀 리더/아키텍트

**학습 내용**:
1. GitHub Action으로 PR 자동화
2. 팀 규칙 표준화
3. 지식 축적 프로세스

**실습**:
```bash
# claude-docs-update.yml 설정
# 팀 CLAUDE.md 규칙 정립
```