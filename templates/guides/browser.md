# 브라우저 작업

## 15. 브라우저 작업 — Aside 우선

적용 조건: 웹 탐색, 로그인된 사이트 조작, 랜딩/웹 UI 시각 검수, 웹 스크린샷, 폼·클릭 흐름 확인.

- 브라우저 작업은 **Aside**로 한다. 우선순위는 (1) Aside MCP `exec`/`repl`, (2) 터미널 `aside "…"` / `aside repl "…"`이다. CLI 경로는 `~/.local/bin/aside`다.
- 대부분의 작업은 `aside exec` 또는 `aside "…"`로 에이전트에 맡기고, DOM·스크린샷·수치 확인이 필요하면 `aside repl`을 쓴다.
- 세션은 `aside session resume|steer|queue|stop <id>`로 이어가거나 제어한다. 사용법 확인에는 `aside guide`를 쓴다.
- 결제·은행·공공 사이트는 **Safari**에서 사용자가 직접 처리한다. Aside에 맡기지 않는다.
- Codex `playwright` skill·MCP, `playwright-cli`, `@playwright/test`, Puppeteer를 Aside 대신 사용하지 않는다. `mcp_servers.playwright`는 비활성 상태를 유지하며 이 정책을 이유로 기존 테스트·의존성을 삭제하거나 설정을 재작성하지 않는다.
- Playwright를 새로 설치·복구하거나 우회 스크립트로 사용하지 않는다. 예외는 사용자가 이번 작업에서 Playwright를 명시한 경우뿐이다.
- Aside를 사용할 수 없으면 승인되지 않은 브라우저 대안으로 우회하지 말고, 공통 막힘 처리 기준을 따른다.
