---
name: ai-cleanup
description: Plan, trash, encrypt, verify, and restore AI-created backups, test/scratch outputs, build artifacts, and unused images. Use at the end of work that created such files or when the user asks for cleanup.
allowed-tools: Bash(python3 ${CODEX_HOME_DIR}/skills/ai-cleanup/ai_cleanup.py *)
---

# 정리 스킬 (Claude Code 래퍼)

적용 범위·자동 범주·확인 대상·보호 경로·보고는 `~/.claude/CLAUDE.md`의 "생성 파일 정리"와 "실행과 승인"이 정한다. 스크립트·설정·기록·절차의 정본은 Codex 쪽이다:

- 절차 전체: `${CODEX_HOME_DIR}/skills/ai-cleanup/SKILL.md` — 실행 전 필요한 절을 읽는다. 그 문서의 "AGENTS.md sections 2, 6, 9"는 CLAUDE.md의 같은 주제 섹션으로 읽는다.
- 스크립트: `python3 ${CODEX_HOME_DIR}/skills/ai-cleanup/ai_cleanup.py` (설정 `cleanup.toml`, 기록 `~/.codex/maintenance/`)
- 비파괴 회귀 확인: 그 디렉터리에서 `python3 -B verify_non_destructive.py`

## 자동 경로 (확인 불필요, 하루 1회)

```sh
python3 ${CODEX_HOME_DIR}/skills/ai-cleanup/ai_cleanup.py --auto
```

`--dry-run`은 요청 시. 결과의 `summary`, 이동 위치, `restore` 명령, `confirm_tier_by_category`를 보고한다.

## 확인이 필요한 경로

1. 계획: 인자 없음 또는 `--stage plan` → `plan_id`, 범주별 개수/용량, `needs_user_confirm`, `limits_exceeded`를 보여주고 승인을 기다린다.
2. 아카이브: `--stage archive --plan <file>` (tar→zstd→age, gitleaks, cleanup.toml에 지정한 비공개 백업 저장소)
3. 검증: `--stage verify --plan <file>` (재다운로드 SHA256·복호화 멤버 대조)
4. 이동: `--stage delete --plan <file> --confirm <plan_id>` (사용자가 그 plan_id를 승인한 경우만)
5. 복원: `--stage restore --id <id>`

필수 사전 백업만: `--stage backup --path <files> --reason "<reason>"`. 일반 로컬 백업 사본은 만들지 않는다. 휴지통 이동을 `rm`으로 대체하지 않는다.
