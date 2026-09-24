#!/usr/bin/env python3
"""templates/의 ${VAR}를 .env 값으로 채워 build/에 만든다.
--install을 주면 build/ 결과를 CODEX_HOME_DIR에 복사한다(기존 파일 덮어씀)."""
import pathlib, re, shutil, sys

root = pathlib.Path(__file__).resolve().parent
env = {}
for line in (root / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

build = root / "build"
shutil.rmtree(build, ignore_errors=True)
missing = set()
for src in (root / "templates").rglob("*"):
    if not src.is_file():
        continue
    def fill(m):
        if m.group(1) not in env or not env[m.group(1)]:
            missing.add(m.group(1))
            return m.group(0)
        return env[m.group(1)]
    out = build / src.relative_to(root / "templates")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(re.sub(r"\$\{([A-Z_]+)\}", fill, src.read_text()))
if missing:
    sys.exit(f".env에 값이 없음: {', '.join(sorted(missing))}")
print(f"렌더링 완료: {build}")

if "--install" in sys.argv:
    dest = pathlib.Path(env["CODEX_HOME_DIR"])
    shutil.copytree(build, dest, dirs_exist_ok=True)
    print(f"설치 완료: {dest} (config.agents.toml 내용은 config.toml에 직접 추가)")
