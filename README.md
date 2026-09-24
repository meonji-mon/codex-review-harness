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

## 설치

### 준비물

- [Codex CLI](https://github.com/openai/codex) (확인한 버전: 0.156.1)
- Python 3.8 이상 (`render.py`는 표준 라이브러리만 사용)
- Git

### 1. 내려받기

```bash
git clone https://github.com/meonji-mon/codex-review-harness.git
```

```bash
cd codex-review-harness
```

### 2. `.env` 채우기

```bash
cp .env.example .env
```

| 변수 | 들어갈 값 | 예시 |
|---|---|---|
| `CODEX_HOME_DIR` | Codex 설정 폴더 (`CODEX_HOME`을 따로 쓰지 않으면 `~/.codex`의 절대 경로) | `/Users/me/.codex` |
| `USER_HOME` | 홈 폴더 절대 경로 | `/Users/me` |
| `APPLE_DEVELOPER_EMAIL` | Apple Developer 계정 이메일 | `me@example.com` |
| `ADMOB_EMAIL` | Google AdMob 계정 이메일 | `me@example.com` |
| `APPS_IN_TOSS_EMAIL` | 앱인토스 계정 이메일 | `me@example.com` |
| `ASC_API_ISSUER_ID` | App Store Connect API Issuer ID | `00000000-0000-0000-0000-000000000000` |

계정 값은 `guides/release-accounts.md`에서 대상 계정을 구분하는 데만 쓰인다. 해당 서비스를 쓰지 않으면 아무 값이나 넣어도 되지만 비워 두면 렌더링이 멈춘다. `.env`는 `.gitignore`에 들어 있어 커밋되지 않는다.

### 3. 렌더링하고 결과 확인

```bash
python3 render.py
```

`build/`에 값이 채워진 완성본이 생긴다. 이 단계는 `~/.codex`를 건드리지 않는다. `.env`에 빠진 값이 있으면 변수 이름을 알려 주고 멈춘다.

설치 전에 `build/AGENTS.md`와 `build/guides/`를 읽어 보고 자기 환경에 맞게 고친다. 이 지침은 만든 사람의 환경(MEONJI 브랜드·스플래시 규격, Aside 브라우저, 지정 시뮬레이터, opencodex 모델 이름)을 전제로 한다. 고칠 때는 `templates/`를 고친 뒤 다시 렌더링한다.

### 4. 기존 설정 백업

`--install`은 같은 이름의 파일을 **덮어쓴다**. 설치로 바뀌는 파일만 백업한다. `~/.codex` 전체를 복사하면 세션 기록까지 복사돼 매우 클 수 있다.

```bash
mkdir -p ~/codex-harness-backup
```

```bash
cd ~/.codex && cp -R AGENTS.md review guides agents instructions config.toml ~/codex-harness-backup/ 2>/dev/null; ls ~/codex-harness-backup
```

없는 파일은 건너뛴다.

직접 쓴 전역 지침이 있다면 통째로 덮지 말고 `build/AGENTS.md`의 7절(검수 에이전트와 구현 책임)과 "작업별 지침 읽기" 절만 옮겨 붙이는 방법도 있다.

### 5. 설치

```bash
python3 render.py --install
```

`build/`의 내용이 `CODEX_HOME_DIR`로 복사된다. 결과 위치는 다음과 같다.

| 파일 | 설치 위치 |
|---|---|
| `AGENTS.md` | `~/.codex/AGENTS.md` |
| `review/`, `guides/` | `~/.codex/review/`, `~/.codex/guides/` |
| `agents/ui_reviewer.toml`, `agents/code_reviewer.toml` | `~/.codex/agents/` |
| `instructions/agent-harness.md` | `~/.codex/instructions/` |

### 6. 검수 역할 등록

`config.agents.toml`의 두 블록을 `~/.codex/config.toml` 끝에 붙인다. `[agents]` 표에서 `enabled = true`인지도 확인한다.

```toml
[agents.ui_reviewer]
config_file = "./agents/ui_reviewer.toml"

[agents.code_reviewer]
config_file = "./agents/code_reviewer.toml"
```

`config.toml`에는 API 키 같은 값이 들어 있을 수 있으므로 이 저장소에 올리지 않는다.

### 7. 동작 확인 (스모크 테스트)

새 터미널에서 실행한다. 이미 열린 Codex 세션은 예전 지침을 쓴다.

```bash
codex exec --skip-git-repo-check -C ~ - < ~/.codex/review/SMOKE_TEST.md
```

두 검수 역할을 `gpt-6-sol` high로 한 번씩 호출하고, `~/.codex/sessions/`의 실행 기록으로 역할·모델·권한·독립성을 표로 보고한다. 모델 호출 비용이 조금 든다. 확인할 것은 다음과 같다.

- 역할 호출·지침 적용·모델 행이 `확인`
- 절차적 독립성이 `CONFIRMED`
- 두 검수자가 읽은 표식이 `REVIEW_ROLE_SMOKE_V13_20260924`

다른 모델을 쓰는 환경이면 `SMOKE_TEST.md`와 `AGENTS.md` 7절의 모델 이름을 먼저 바꾼다.

### 되돌리기

백업한 파일을 다시 복사한다.

```bash
cp -R ~/codex-harness-backup/. ~/.codex/
```

설치 전에 없던 폴더(`review/`, `guides/` 등)는 이 명령으로 지워지지 않는다. 필요하면 직접 지운다.

## 알려진 한계

- 역할 TOML의 `sandbox_mode = "read-only"`는 부모 세션 권한에 덮여 적용되지 않는다. 검수자의 쓰기 금지는 지침으로만 막힌다.
- Fast(`service_tier = "priority"`)는 응답에 `default`로 표시되지만 실측 속도는 약 1.4배였다.
