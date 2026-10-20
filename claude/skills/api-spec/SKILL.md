---
name: api-spec
description: Write or update page-level frontend-to-backend JSON specs (docs/api-spec/<page_id>.json and index.json) when a real UI diff exists or the user requests it.
allowed-tools: Bash(python3 ${CODEX_HOME_DIR}/harness/ui_change_detect.py *), Bash(python3 ${CODEX_HOME_DIR}/skills/api-spec/validate.py *)
---

# 페이지 API 스펙 (Claude Code 래퍼)

적용 조건은 `~/.claude/CLAUDE.md` "코드 그래프와 문서": 실제 UI diff 또는 사용자 요청일 때만. 문서·빌드·테스트·설정 변경만으로는 만들지 않는다. 문구·간격·색·타이포만 바뀌면 기존 `change`만 갱신하고 새 스펙은 만들지 않는다. 인증·인가·결제·삭제 화면이나 그런 API가 `needed`/`changed`면 code-reviewer 리뷰가 필요하다.

형식·추적 방법의 정본: `${CODEX_HOME_DIR}/skills/api-spec/SKILL.md` (작성 전 "Identify pages", "Trace contracts", "Format" 절을 읽는다). 단, 그 문서의 Laya 기록(`laya_classify.py --log-decision`) 단계는 Claude Code에서는 하지 않는다.

1. 페이지 찾기: `python3 ${CODEX_HOME_DIR}/harness/ui_change_detect.py --project <절대 앱 루트> [--base <시작 커밋>]`
2. 계약 추적: Flutter는 callgraph `screen_to_backend`/`widget_usage`, Expo/React/SwiftUI는 import→데이터 계층을 따라가고 근거를 `evidence`에 남긴다.
3. 작성: `docs/api-spec/<page_id>.json`, 스키마 `${CODEX_HOME_DIR}/skills/api-spec/api-spec.schema.json`. 모르는 계약은 `null` + `open_questions`. 다른 `index.json` 항목은 보존한다.
4. 검증: `python3 ${CODEX_HOME_DIR}/skills/api-spec/validate.py docs/api-spec`
