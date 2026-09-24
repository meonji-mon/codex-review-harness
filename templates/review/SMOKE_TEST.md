## 목표

설치한 두 검수 역할(`ui_reviewer`, `code_reviewer`)이 실제로 로딩·호출되고, 지정 모델과 읽기 전용 권한으로 독립 실행되는지 확인한다. 제품 PASS/BLOCK 판정이 아니다.

## 범위

- 읽을 파일: `${CODEX_HOME_DIR}/AGENTS.md`, `${CODEX_HOME_DIR}/review/activation.md`, `${CODEX_HOME_DIR}/review/dispatch.md`, `${CODEX_HOME_DIR}/agents/ui_reviewer.toml`, `${CODEX_HOME_DIR}/agents/code_reviewer.toml`, `${CODEX_HOME_DIR}/config.toml`의 `[agents.*]` 항목
- 검수자에게 줄 자료: `${CODEX_HOME_DIR}/review/SMOKE_EVIDENCE.md` 하나
- 확인할 기록: `${CODEX_HOME_DIR}/sessions/`의 이번 부모·자식 rollout

## 하지 말 것

- 파일·설정 수정, 설치, 테스트 실행, 배포, Notion·원격 쓰기, 앱 조작
- 부모 모델 변경, 지원되지 않는 모델을 다른 모델로 대체, 역할 가장
- 검수자 패킷에 부모 추론이나 다른 검수자 결론 넣기
- 확인하지 못한 값을 요청값으로 채우기

## 절차

1. 범위의 파일을 읽고, 현재 작업 경로에 `AGENTS.override.md`나 동명 역할 파일이 있으면 경로만 적는다.
2. `ui_reviewer`, `code_reviewer`를 각 한 번 호출한다. 호출 인자에 `model: gpt-6-sol`, `reasoning_effort: high`, `fork_turns: none`을 명시한다.
3. 각 검수자에게 `${CODEX_HOME_DIR}/review/SMOKE_EVIDENCE.md`를 읽고 역할 ID, 읽은 표식, 제품 파일 수정 여부만 반환하게 한다.
4. `${CODEX_HOME_DIR}/review/activation.md`의 "Codex 로컬 기록에서 확인하는 방법"대로 부모·자식 rollout을 읽어 각 항목을 확인한다.

## 실패 시 중단

역할 호출이 거부되거나 `gpt-6-sol`을 쓸 수 없으면 그 상태를 보고하고 끝낸다. 기록으로 확인할 수 없는 항목은 `UNVERIFIED`로 두고 같은 호출을 반복하지 않는다.

## 완료 기준

아래 표의 모든 행이 근거와 함께 `확인` 또는 `UNVERIFIED`로 채워졌다.

## 출력 형식

| 항목 | 결과 | 근거 (파일 경로·필드·세션 ID) |
|---|---|---|
| 파일 배치 | | |
| 역할 등록 (`config.toml`의 `[agents.ui_reviewer]`, `[agents.code_reviewer]`) | | |
| 역할 호출 (`session_meta.agent_role`) | | |
| 역할 지침 적용 (자식 developer 지침의 하네스 버전 표식) | | |
| 실제 모델·effort (자식 `turn_context`) | | |
| 읽기 전용 (자식 `sandbox_policy`) | | |
| 컨텍스트 분리 (`fork_turns`, 부모 대화 미복제) | | |
| 절차적 독립성 | CONFIRMED / UNVERIFIED | |
| 검수자가 읽은 표식 | | |

표 아래에 미확인 항목과 그 이유만 짧게 적는다.
