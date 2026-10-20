---
name: baton
description: Coordinate the current model with the light-worker (gpt-6.1-sol low via opencodex) only when the user invokes /baton or explicitly requests Sol Light delegation.
disable-model-invocation: true
---

# Baton 위임 (Claude Code)

메인은 조율·통합·판단, `light-worker` 서브에이전트(opencodex `ocx-claude-native--gpt-6.1-sol`, low)는 편집·실행을 맡는다. 메인은 실패한 패치를 직접 떠맡지 않는다: 원인을 진단하고 범위/지시를 고쳐 다시 배정하며, 두 번 실패하면 보고한다. light-worker를 쓸 수 없으면 다른 모델로 대체하지 않고 보고한다. 고위험 변경의 필수 리뷰(code-reviewer)는 그대로 필요하다.

각 brief에 담을 것:
1. 목표와 Done when
2. 소유 파일·범위·필수 참고
3. 금지 변경과 보존할 기존 작업
4. 번호 매긴 실행/검사 단계
5. 기대 결과와 실패 시 돌려줄 근거

독립 작업은 소유권·의존성을 연결하고, 앞 결과를 뒤 brief에 넘긴다. 실제 경로·diff·원본 검사·남은 문제를 통합해 보고한다. 절차 정본: `${CODEX_HOME_DIR}/skills/baton/SKILL.md`.
