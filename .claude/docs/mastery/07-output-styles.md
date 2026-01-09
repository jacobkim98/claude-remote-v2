# 7. Output Styles (출력 스타일)

> 이 문서는 [CLAUDE-CODE-MASTERY.md](../CLAUDE-CODE-MASTERY.md)의 일부입니다.

---

## 7.1 출력 스타일이란?

**출력 스타일**은 Claude Code의 응답 형식을 커스터마이즈하는 기능입니다. 기본 제공 스타일을 사용하거나 커스텀 스타일을 정의할 수 있습니다.

---

## 7.2 기본 제공 스타일

| 스타일 | 설명 | 사용 사례 |
|--------|------|----------|
| **Default** | 표준 출력 | 일반적인 대화 |
| **Explanatory** | 상세 설명 포함 | 학습, 이해 필요 시 |
| **Learning** | 교육적 설명 | 새로운 개념 학습 |
| **Concise** | 간결한 응답 | 빠른 작업, 경험자 |
| **Verbose** | 최대 상세도 | 복잡한 디버깅 |

**스타일 적용**:

```bash
# 세션 시작 시 스타일 지정
claude --output-style concise

# 세션 중 변경
/style concise
```

---

## 7.3 커스텀 스타일 정의

**위치**: `.claude/styles/{style-name}.md`

**템플릿**:

```markdown
---
name: my-style
description: 나만의 출력 스타일
---

# Output Style Instructions

## 톤과 형식
- 간결하고 직접적으로 답변
- 불필요한 서론 생략
- 코드 예시 우선

## 구조
- 핵심 내용 먼저
- 추가 설명은 접기(collapse) 사용
- 관련 파일 경로 항상 표시

## 포맷팅
- 마크다운 사용
- 코드 블록에 언어 명시
- 테이블로 비교 정리
```

---

## 7.4 스타일 활용 예시

**간결한 코드 리뷰 스타일**:

```markdown
---
name: brief-review
description: 핵심만 짚는 코드 리뷰
---

# Brief Review Style

## 형식
- 문제점만 나열 (잘된 점 생략)
- 수정 코드 바로 제시
- 1-2줄 설명

## 예시 출력
❌ `any` 타입 사용 → `string | number`로 수정
❌ 미사용 변수 `temp` 삭제
⚠️ 에러 핸들링 추가 권장
```

**교육용 스타일**:

```markdown
---
name: teaching
description: 개념 설명 중심
---

# Teaching Style

## 형식
- 코드 전에 개념 설명
- 왜(Why) 설명 필수
- 단계별 진행
- 실수하기 쉬운 부분 강조

## 구조
1. 개념 소개
2. 간단한 예시
3. 실제 적용
4. 주의사항
```