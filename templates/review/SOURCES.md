# 근거·적용 범위·미확인 자료

확인일: 2026-09-24. API·런타임 동작은 적용 시 설치 버전과 유효 설정을 다시 확인한다. 아래 문서는 설계 참고 자료이며 실행 지침에 매번 모두 읽도록 추가하지 않는다.

## 공식 OpenAI 자료

[S0] Custom instructions with AGENTS.md — `https://learn.chatgpt.com/docs/agent-configuration/agents-md`

전역·프로젝트 지침의 발견/결합 순서, 적용 경로, 코드 검수 규칙, 합산 크기 제한을 확인했다. 패키지는 공통 지침과 작업별 참조를 나눴다. 파일 존재나 본문의 “적용 조건”만으로 실제 로딩·토큰 절감이 보장된다고 표시하지 않았다.

[S1] Subagents — `https://learn.chatgpt.com/docs/agent-configuration/subagents`

사용자 정의 에이전트의 standalone TOML, `name`·`description`·`developer_instructions`, `sandbox_mode`, 모델/effort 상속과 오버라이드, `[agents].enabled`, 부모 런타임 권한 상속을 확인했다. 이 스키마를 사용하되 실제 Codex에서 로드·실행한 것은 아니다. 좁은 역할과 도구 권한에 맞춘 별도 지침을 적용했다.

[S2] Model guidance / Using GPT-6 — `https://developers.openai.com/api/docs/guides/latest-model`

GPT-6 Astra·Sol·Luna, 공통 프롬프트 출발점, Astra 행동을 다른 모델에 적용할 때의 평가 필요성을 확인했다. 명확한 위임 조건·범위에 맞는 검증·결과 중심 지시를 반영했다. 모델마다 독립적으로 발행된 전체 검수 프롬프트라고 표현하지 않았다.

[S3] GPT-6 Luna — `https://developers.openai.com/api/docs/models/gpt-6-luna`

[S4] GPT-6 Sol — `https://developers.openai.com/api/docs/models/gpt-6-sol`

[S5] GPT-6 Astra — `https://developers.openai.com/api/docs/models/gpt-6-astra`

공식 모델 ID와 설명을 확인하고 모델별 입력 조정의 근거로 사용했다. 실제 계정의 모델 사용 권한, 검수 정확도나 비용 순위를 측정한 자료는 아니다.

## 공식 Anthropic 자료

[S6] Create custom subagents — `https://code.claude.com/docs/en/sub-agents`

역할별 별도 컨텍스트·시스템 프롬프트·도구 제한, 읽기 전용 코드 검수 패턴을 개념적으로 참고했다. Claude Code의 YAML·permissionMode·도구 이름을 Codex TOML에 그대로 복사하지 않았다. 두 런타임의 권한 동작이 같다고 가정하지 않았다.

[S7] Prompting Claude Opus 5.5 — `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5`

붙여 넣은 자료와 사용자의 지시를 구분하는 원칙, 원본 시각 자료와 필요한 확대/크롭, 추상적인 미감 대신 구체적인 디자인 조건을 참고했다. 이 패키지에는 자료 경계·실제 화면 증거·승인된 토큰/레퍼런스 중심 검수로 반영했다. 시스템 프롬프트 복제나 비공개 지침 확인을 의미하지 않는다.

## 사용자 제공 비공식 링크: 본문 미확보

`https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/CLAUDE-OPUS-5.5.md`

GitHub 연결 도구로 파일 읽기를 시도했지만 본문은 빈 값으로 반환됐다. raw 읽기도 파일 내용 반환에 실패했고, 웹에서는 파일 페이지의 메타데이터만 확인할 수 있었다. 본문을 읽거나 비교·인용·검증한 자료로 계산하지 않았다. 실제 유출된 시스템 프롬프트인지도 확인하지 못했다. 따라서 이 파일에서 지침을 추출했다고 표시하지 않으며, 공식 Anthropic 자료 [S6][S7]을 별도로 참고했다.

## 사용자 원본

기준은 첨부 `Codex_맞춤_지침_최종본.md`와 `Codex_맞춤_지침_조건부_패키지.zip`이다. 7절의 검수 구조, 적용 방식의 역할 구분, TestFlight의 검수 참조만 조정했다. 브랜드·스플래시·계정 식별값·시뮬레이터·이미지·Aside·기존 하네스 경로 등은 요구 보존 대상으로 취급했다. 그 도구·모델·계정이 사용자 환경에서 실제 동작한다는 추가 검증은 하지 않았다.

## v1.2 추가 확인 — 크기 예산과 실제 로딩

확인일: 2026-09-24. 다음 공식 OpenAI 저장소의 동일 커밋에서 구현을 확인했다. 공개 소스를 읽은 것이며 사용자의 설치 바이너리가 같은 버전임을 확인한 것은 아니다.

[S8] OpenAI Codex, global user instructions provider.
`https://github.com/openai/codex/blob/29f056c26c09b51db123069ed3ec2095b227d6db/codex-rs/codex-home/src/instructions/mod.rs`

`load_from_codex_home`은 Codex home의 override/기본 후보에서 비어 있지 않은 전역 지침을 읽어 전달한다. 이 코드 경로는 프로젝트 바이트 예산을 인자로 받거나 차감하지 않는다.

[S9] OpenAI Codex, project AGENTS.md loading and assembly.
`https://github.com/openai/codex/blob/29f056c26c09b51db123069ed3ec2095b227d6db/codex-rs/core/src/agents_md.rs`

`load_project_instructions`는 주어진 사용자 지침으로 시작한 뒤 project_doc_max_bytes를 remaining에 별도로 설정한다. 프로젝트 지침 항목의 길이를 차감하며 `read_agents_md`에서 남은 예산 초과 시 잘라 읽고 경고를 기록한다. 따라서 이 구현에서 전역 사용자 지침과 프로젝트 파일의 단순 합산을 해당 제한 사용량으로 설명하지 않는다. 전역 경로가 프로젝트 발견 경로와 겹치는 특수 배치나 다른 호스트의 동작은 따로 확인해야 한다.

[S10] OpenAI Codex configuration reference.
`https://learn.chatgpt.com/docs/config-file/config-reference`

프로젝트 지침 예산과 설정 설명을 확인했다. 활성 프로필·CLI·호스트의 유효 설정은 로컬 확인 대상이다. v1.2 점검 도구는 모든 설정 레이어를 해석하는 공식 로더를 복제한 것이 아니다.

[S0] AGENTS.md 안내와 [S1] Subagents 안내는 이번 작업에서도 다시 읽었다. 시작/세션 로그로 로딩을 감사할 수 있다는 안내와 부모의 live runtime override가 서브에 적용될 수 있다는 경계를 반영했다. 단순 질문 응답을 가장 강한 자동 주입 증거로 보지 않는 판단과 절차적 독립성의 세 기준은 이 패키지의 설계다.

기존 [S2]–[S7] 모델·Anthropic 참고 내용은 이전 패키지에서 보존했다. v1.2에서 각 모델을 호출하거나 새 모델 비교를 수행한 것은 아니다.
