# Codex 검수 하네스

Codex용 전역 지침(`AGENTS.md`)과 듀얼 검수 역할(`ui_reviewer`, `code_reviewer`) 하네스.

- 독립 검수는 고위험 변경(인증·권한·결제, 데이터 삭제/이관, 공유 API 파괴, 앱 시작·서명 위험)일 때만 의무
- 모델 기본값: 명확한 작업은 GPT-6 Luna Max + Fast, 모호한 작업은 Sol high, 검수·디자인 목업은 Astra/Sol high
- 절차적 독립성은 `~/.codex/sessions/` rollout 기록으로 확인 (`review/activation.md`)

## 구성

| 경로 | 설치 위치 |
|---|---|
| `templates/AGENTS.md` | `~/.codex/AGENTS.md` |
| `templates/review/`, `templates/guides/` | `~/.codex/review/`, `~/.codex/guides/` |
| `templates/agents/*.toml` | `~/.codex/agents/` |
| `templates/instructions/agent-harness.md` | `~/.codex/instructions/` |
| `config.agents.toml` | `~/.codex/config.toml`에 직접 추가 |

개인 경로·계정 식별값은 `${VAR}` 자리표시자로 되어 있고 실제 값은 `.env`(Git 제외)에 둔다.

## 사용

```bash
cp .env.example .env   # 값 채우기
python3 render.py            # build/에 결과 생성
python3 render.py --install  # CODEX_HOME_DIR에 복사 (기존 파일 덮어씀)
```

## 알려진 한계

- 역할 TOML의 `sandbox_mode = "read-only"`는 부모 세션 권한에 덮여 적용되지 않는다. 검수자의 쓰기 금지는 지침으로만 막힌다.
- Fast(`service_tier = "priority"`)는 응답에 `default`로 표시되지만 실측 속도는 약 1.4배였다.
