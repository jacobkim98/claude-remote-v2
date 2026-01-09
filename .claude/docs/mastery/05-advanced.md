# 5. 최신 트렌드 분석 및 실행 워크플로우

> 이 문서는 [CLAUDE-CODE-MASTERY.md](../CLAUDE-CODE-MASTERY.md)의 일부입니다.

---

## 5.1 최신 트렌드 분석 방법

### Claude Code가 수행할 분석

**명령어**: `/upgrade-claude-code` 실행 시

```markdown
## 분석 단계

### 1단계: 최신 정보 수집 (WebSearch)
- "Claude Code best practices {current_year}"
- "Claude Code configuration tips"
- "Boris Cherny Claude Code"
- "Claude MCP servers latest"
- "{detected_language} Claude Code setup"

### 2단계: 현재 설정 분석
- 기존 .claude/ 구조 파악
- CLAUDE.md 내용 분석
- 누락된 설정 식별

### 3단계: 개선 제안
- 새로운 기능 추천
- 설정 최적화 방안
- 트렌드 반영 업그레이드
```

### 분석 결과 형식

```markdown
## Claude Code 업그레이드 분석 결과

### 현재 상태
| 항목 | 상태 | 점수 |
|------|------|------|
| CLAUDE.md | ✅ | 8/10 |
| Commands | ✅ | 7/10 |
| Agents | ✅ | 6/10 |
| Skills | ❌ | 0/10 |
| Hooks | ✅ | 9/10 |

### 권장 업그레이드
1. **[높음]** Skills 폴더 추가
2. **[중간]** 새로운 MCP 서버 연결
3. **[낮음]** 커맨드 추가

### 최신 트렌드
- {트렌드 1 설명}
- {트렌드 2 설명}
```

---

## 5.2 실행 워크플로우

### /learn-claude-code 워크플로우

```
시작
  ↓
이 문서(CLAUDE-CODE-MASTERY.md) 읽기
  ↓
현재 .claude/ 구조 분석
  ↓
사용자 레벨 추정 (1-4)
  ↓
해당 레벨 교육 콘텐츠 제공
  ↓
실습 가이드 + 코드 예시 제공
  ↓
다음 레벨 안내
```

### /setup-claude-code 워크플로우

```
시작
  ↓
이 문서(CLAUDE-CODE-MASTERY.md) 읽기
  ↓
프로젝트 분석
  ├── 언어 감지 (package.json, go.mod, Cargo.toml 등)
  ├── 구조 감지 (모노레포, 마이크로서비스 등)
  └── 기존 설정 확인
  ↓
적합한 템플릿 선택
  ↓
파일 생성
  ↓
결과 요약 출력
```

### /upgrade-claude-code 워크플로우

```
시작
  ↓
이 문서(CLAUDE-CODE-MASTERY.md) 읽기
  ↓
현재 설정 분석 및 점수 산출
  ↓
WebSearch로 최신 트렌드 조사
  ↓
개선점 식별 및 우선순위화
  ↓
사용자에게 제안
  ↓
승인 시 업그레이드 적용
  ↓
결과 요약
```