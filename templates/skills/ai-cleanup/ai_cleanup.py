#!/usr/bin/env python3
"""ai_cleanup: dry-run-first cleanup of AI-made backups, test/scratch output, build artifacts and unused images.

Stages (default: plan):
  plan     scan and write <state_dir>/cleanup-plan-<ts>.json; changes nothing.
  archive  --plan FILE   tar | zstd | age the 'archive_then_trash' items (no plaintext on disk), gitleaks-scan the
                         manifest, upload YYYY/MM/<plan_id>.tar.zst.age + .manifest.json to the private GitHub repo
                         ([archive] repo), re-download + sha256 + decrypt-list check. REFUSES if age, gitleaks, zstd,
                         gh auth, repo or recipient is missing. Leaves no local copy.
  verify   --plan FILE   re-download the uploaded archive, compare sha256, decrypt-list round-trip with the key.
  backup   --path P [P...] --reason TEXT   same encrypted upload for a one-off backup before a high-risk change
                         (id bk-<ts>-<hash>); prints the restore command. Use INSTEAD of local .bak copies.
  delete   --plan FILE --confirm PLAN_ID [--only-category C...]   move eligible items to the Trash folder. Requires the user's
                         explicit confirmation (PLAN_ID from the plan) and, for archive items, a verified archive.
  --auto [--dry-run] [--force]   plan, then move ONLY the auto tier (untracked unreferenced imagegen output,
                         untracked captures in project tmp/output/artifacts, /private/tmp build artifacts+scratch+captures,
                         Desktop screenshots, ~/api-spec-test-*) older than min_age_days, oldest first, in batches of
                         [auto] batch_items up to max_bytes_per_run; throttled to once per min_interval_hours;
                         old managed Trash is reported only; permanent deletion is a separate authorized task.
  restore  --id ID       move items from ~/.Trash/ai-cleanup-ID back to their original paths (never overwrites).
Never: rm, deleting git-tracked files, touching never_touch paths / sessions / live configs / graphify-out.
Config: ~/.codex/skills/ai-cleanup/cleanup.toml (or --config). Stdlib only (Python 3.11+).
"""
import argparse, base64, fnmatch, glob, hashlib, json, os, re, shutil, subprocess, sys, tarfile, tempfile, time, tomllib
import uuid
from pathlib import Path
from cleanup_safety import (SafetyError, SharedProtection, snapshot, same_moved_object,
                            atomic_record, journal_lock, rename_exclusive,
                            recorded_transfer, restoration_state)

HOME = os.path.expanduser("~")
HERE = os.path.dirname(os.path.abspath(__file__))
NOW = time.time()
TEXT_EXT = {".dart", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".swift", ".kt", ".java", ".m", ".mm", ".h",
            ".html", ".htm", ".css", ".scss", ".md", ".mdx", ".json", ".yaml", ".yml", ".plist", ".xml",
            ".storyboard", ".xib", ".gradle", ".arb", ".toml", ".txt", ".csv", ".pbxproj", ".strings",
            ".xcstrings", ".py", ".rb", ".sh", ".vue", ".svelte", ".kts", ".properties", ".svg"}
TOKEN = re.compile(r'[^\s"\'`()<>\[\]{},;:=|*]+')
DYNAMIC = re.compile(r'([\w./@-]*?)(\$\{|\$\w|\\\(|\'\s*\+|"\s*\+|`\s*\+)[^\n]{0,80}?\.(png|jpe?g|webp|gif)', re.I)

def X(p): return os.path.realpath(os.path.expanduser(p))
def short(p): return p.replace(HOME, "~", 1) if p.startswith(HOME) else p

def run(cmd, **kw):
    try: return subprocess.run(cmd, capture_output=True, text=True, **kw)
    except FileNotFoundError: return None

def newest_mtime(p):
    try: m = os.lstat(p).st_mtime
    except OSError: return None
    if os.path.isdir(p) and not os.path.islink(p):
        for r, ds, fs in os.walk(p):
            for f in fs:
                try: m = max(m, os.lstat(os.path.join(r, f)).st_mtime)
                except OSError: pass
    return m

def size_of(p):
    if os.path.isdir(p) and not os.path.islink(p):
        r = run(["du", "-sk", p])
        try: return int(r.stdout.split()[0]) * 1024
        except Exception: return 0
    try: return os.lstat(p).st_size
    except OSError: return 0

def sha256(p, limit=None):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def under(p, roots): return any(p == r or p.startswith(r.rstrip("/") + "/") for r in roots)

def git_root(p):
    d = p if os.path.isdir(p) else os.path.dirname(p)
    r = run(["git", "--no-optional-locks", "-C", d, "rev-parse", "--show-toplevel"], env={**os.environ, "LC_ALL": "C"})
    if r is None: raise SafetyError("Git is unavailable; tracking cannot be verified")
    if r.returncode:
        if "not a git repository" in r.stderr: return None
        raise SafetyError("Git root lookup failed; tracking is unknown")
    return os.path.realpath(r.stdout.strip())

_ROOT_CACHE, _TRACKED_CACHE = {}, {}
def is_tracked(p):
    d = p if os.path.isdir(p) else os.path.dirname(p)
    if d not in _ROOT_CACHE: _ROOT_CACHE[d] = git_root(p)
    root = _ROOT_CACHE[d]
    if not root: return False
    if root not in _TRACKED_CACHE:
        r = run(["git", "--no-optional-locks", "-C", root, "ls-files", "-z"])
        if r is None or r.returncode: raise SafetyError("Git index lookup failed; tracking is unknown")
        _TRACKED_CACHE[root] = {os.path.join(root, x) for x in r.stdout.split("\0") if x}
    t = _TRACKED_CACHE[root]; rp = os.path.realpath(p)
    if rp in t: return True
    if os.path.isdir(rp):  # a folder counts as tracked if anything inside is tracked
        pre = rp.rstrip("/") + "/"
        return any(x.startswith(pre) for x in t)
    return False

def trash_root(cfg):
    """Configured trash dir if writable, else the fallback (macOS may deny ~/.Trash without Full Disk Access)."""
    want = X(cfg.get("trash_dir", "~/.Trash")); fb = X(cfg.get("trash_fallback_dir", "~/.codex/maintenance/trash"))
    try:
        os.listdir(want)
        if not os.access(want, os.W_OK | os.X_OK): raise PermissionError("Trash is not writable")
        return want, None
    except OSError as e:
        return fb, f"{short(want)} unavailable; prospective fallback is {short(fb)}"

def protection(cfg):
    if "_shared_protection" not in cfg: cfg["_shared_protection"] = SharedProtection(cfg)
    return cfg["_shared_protection"]

def protection_reason(cfg, path):
    try: return protection(cfg).reason(path)
    except SafetyError as error: return str(error)

# ---------- backups ----------
def target_key(p):
    d, b = os.path.dirname(p), os.path.basename(p)
    m = re.match(r'(.+?)\.(bak|backup)\b', b) or re.match(r'(.+?)[-_.](bak|backup)([-_.]|$)', b)
    if m and not b.startswith(("backup-", "backups")):
        return os.path.join(d, m.group(1))
    toks, keep = re.split(r'[-_]', re.sub(r'\.(json|toml|md)$', '', b)), []
    for i, t in enumerate(toks):
        if re.fullmatch(r'\d{6,}.*|v\d+|before|[0-9a-f]{8,}|\d+\.\d+(\.\d+)?', t) or \
           (i == len(toks) - 1 and i > 0 and re.fullmatch(r'(?=.*\d)[A-Za-z0-9]{6}', t)):
            break
        keep.append(t)
    return os.path.join(d, "-".join(keep) or b)

def expand(globs, excl=()):
    out = []
    for g in globs:
        base = os.path.realpath(os.path.expanduser(re.split(r'[*?\[]', g, maxsplit=1)[0]).rsplit("/", 1)[0] or "/")
        for p in glob.glob(os.path.expanduser(g), recursive=True):
            rp = os.path.realpath(p)
            if os.path.islink(p) or not (rp == base or rp.startswith(base.rstrip("/") + "/")): continue
            if any(fnmatch.fnmatch(rp, X(e)) or fnmatch.fnmatch(p, os.path.expanduser(e)) for e in excl): continue
            out.append(rp)
    return sorted(set(out))

# ---------- images ----------
def find_projects(cfg):
    ic, roots = cfg["images"], []
    for base in ic.get("project_roots", []):
        base = X(base)
        for r, ds, fs in os.walk(base):
            depth = r[len(base):].count(os.sep)
            if ".git" in ds:
                gitdir = os.path.join(r, ".git")
                act = max((os.path.getmtime(os.path.join(gitdir, f)) for f in ("index", "HEAD", "logs/HEAD", "FETCH_HEAD", "ORIG_HEAD")
                           if os.path.exists(os.path.join(gitdir, f))), default=0)
                lc = run(["git", "--no-optional-locks", "-C", r, "log", "-1", "--format=%ct"])
                if lc and lc.stdout.strip().isdigit(): act = max(act, int(lc.stdout.strip()))
                if NOW - act > ic.get("project_active_days", 30) * 86400:  # uncommitted work counts as activity
                    stt = run(["git", "--no-optional-locks", "-C", r, "status", "--porcelain", "-uno"])
                    for line in (stt.stdout.splitlines()[:300] if stt else []):
                        fp = os.path.join(r, line[3:].strip().strip('"'))
                        try: act = max(act, os.path.getmtime(fp))
                        except OSError: pass
                if NOW - act <= ic.get("project_active_days", 30) * 86400: roots.append(r)
            ds[:] = [x for x in ds if x not in ic["skip_dirs"] and not x.startswith(".")] if depth < ic.get("project_max_depth", 4) else []
    roots += [X(p) for p in ic.get("extra_projects", [])]
    roots = sorted(set(roots))
    return [r for r in roots if not any(r != o and r.startswith(o + "/") for o in roots)]  # outermost repo covers nested

def scan_project(root, cfg):
    ic = cfg["images"]; exts = tuple(ic["extensions"]); skip = set(ic["skip_dirs"])
    images, tokens, dyn_dirs = [], set(), set()
    for r, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if d not in skip]
        images += [os.path.join(r, f) for f in fs if f.lower().endswith(exts)]
    spaced = {n for p in images for n in image_names(p) if " " in n}
    found_spaced = set()
    for r, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if d not in skip]
        in_set = r.endswith((".imageset", ".appiconset"))
        for f in fs:
            p = os.path.join(r, f); low = f.lower()
            if low.endswith(exts): continue
            ext = os.path.splitext(low)[1]
            if ext not in TEXT_EXT or (in_set and f == "Contents.json"): continue
            try:
                if os.path.getsize(p) > 3_000_000: continue
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except OSError: continue
            if spaced:
                lt = txt.lower()
                found_spaced |= {n for n in spaced if n in lt}
            for t in TOKEN.findall(txt):
                for piece in t.split("/"):
                    if piece: tokens.add(piece.lower())
            for m in DYNAMIC.finditer(txt):
                if m.group(1): dyn_dirs.add(m.group(1).strip("./").lower())
    tracked = set()
    r = run(["git", "--no-optional-locks", "-C", root, "ls-files", "-z"])
    if r and r.returncode == 0:
        tracked = {os.path.join(root, x) for x in r.stdout.split("\0") if x}
    tokens |= found_spaced
    return images, tokens, dyn_dirs, tracked

def image_names(p):
    b = os.path.basename(p).lower(); stem = re.sub(r'@\dx$', '', os.path.splitext(b)[0])
    names = {b, stem}
    parent = os.path.basename(os.path.dirname(p))
    if parent.endswith((".imageset", ".appiconset")): names.add(parent.rsplit(".", 1)[0].lower())
    return {n for n in names if len(n) >= 3}

def image_refs(p, tokens):
    return any(n in tokens for n in image_names(p))

# ---------- plan ----------
def plan(cfg, args):
    min_age = cfg.get("min_age_days", 14) * 86400
    items, seen = [], set()

    def add(path, category, action, reason, **extra):
        if path in seen: return
        seen.add(path)
        guarded = protection_reason(cfg, path)
        m = os.lstat(path).st_mtime if guarded and os.path.lexists(path) else newest_mtime(path)
        if m is None: return
        age = (NOW - m) / 86400
        it = {"path": short(path), "category": category, "action": action, "reason": reason,
              "size": size_of(path), "age_days": round(age, 1), "mtime": int(m)}
        it.update(extra)
        if guarded:
            it.update(action="keep", reason=guarded)
        elif not category.startswith("image_project") and is_tracked(path):
            it.update(action="keep", reason="git-tracked")
        elif action not in ("keep", "needs_user_confirm") and NOW - m < min_age:
            it.update(action="keep", reason=f"younger than {cfg.get('min_age_days', 14)} days")
        if it["action"] in ("trash", "archive_then_trash"):
            try:
                it["fingerprint"] = snapshot(path)
                it["policy_revision"] = protection(cfg).revision()
                if time.time() * 1e9 - it["fingerprint"]["newest_mtime_ns"] < min_age * 1e9:
                    it.update(action="keep", reason="tree contains recent entries")
                guarded = protection_reason(cfg, path)
                if guarded: it.update(action="keep", reason=guarded)
            except (OSError, SafetyError) as error:
                it.update(action="keep", reason="source snapshot unavailable: " + str(error))
        items.append(it)

    # backups: keep newest per target
    bk = expand(cfg["backups"]["globs"], cfg["backups"].get("exclude", []))
    groups = {}
    for p in bk: groups.setdefault(target_key(p), []).append(p)
    for key, ps in groups.items():
        ps.sort(key=lambda p: newest_mtime(p) or 0, reverse=True)
        for i, p in enumerate(ps):
            if is_tracked(p): add(p, "backup", "keep", "git-tracked"); continue
            big = size_of(p) > cfg.get("archive_max_item_bytes", 20_000_000)
            if i == 0: add(p, "backup", "keep", "newest backup for target", target=short(key))
            else: add(p, "backup", "needs_user_confirm" if big else "archive_then_trash",
                      "too large to archive" if big else "older backup (archive encrypted first)", target=short(key))
    for p in expand(cfg["test_outputs"]["globs"]):
        add(p, "test_output", "trash", "AI test/scratch output")
    keep_arch = cfg["build_artifacts"].get("keep_recent_archives_days", 30) * 86400
    for p in expand(cfg["build_artifacts"]["globs"]):
        if p.endswith(".xcarchive") and NOW - (newest_mtime(p) or NOW) < keep_arch:
            add(p, "build_artifact", "keep", "recent xcarchive"); continue
        add(p, "build_artifact", "trash", "build output (no archive)")
    for p in expand(cfg["scratch"]["globs"]):
        if os.path.isfile(p): add(p, "scratch", "trash", "AI scratch file in /tmp")

    # images
    ic = cfg["images"]; exts = tuple(ic["extensions"])
    projects = [] if args.no_images else find_projects(cfg)
    all_tokens, proj_img_hashes, proj_img_sizes = set(), {}, {}
    protect = {x.lower() for x in ic.get("protect_dir_names", [])}
    for root in projects:
        t0 = time.time()
        images, tokens, dyn, tracked = scan_project(root, cfg)
        all_tokens |= tokens
        for p in images:
            try: proj_img_sizes.setdefault(os.path.getsize(p), []).append(p)
            except OSError: pass
            if image_refs(p, tokens): continue
            rel = os.path.relpath(p, root).lower()
            maybe_dyn = any(d and (rel.startswith(d) or ("/" + d + "/") in ("/" + rel)) for d in dyn)
            if p in tracked:
                add(p, "image_project_tracked", "needs_user_confirm",
                    "tracked, no reference found" + (" (dir has dynamic image paths)" if maybe_dyn else "") +
                    " -> remove only via a normal code change", project=short(root))
            elif any(seg in protect for seg in rel.split("/")[:-1]):
                add(p, "image_project_untracked", "needs_user_confirm", "store/marketing folder (protected)", project=short(root))
            elif maybe_dyn:
                add(p, "image_project_untracked", "needs_user_confirm", "untracked, dir has dynamic image paths", project=short(root))
            else:
                big = os.path.getsize(p) > cfg.get("large_image_bytes", 5_000_000)
                add(p, "image_large" if big else "image_project_untracked", "trash",
                    "untracked, no reference found", project=short(root))
        print(f"  scanned {short(root)}: {len(images)} images, {time.time()-t0:.1f}s", file=sys.stderr)
    for p in expand(ic["screenshot_globs"]):
        if not os.path.isfile(p) or not p.lower().endswith(exts): continue
        if image_refs(p, all_tokens): add(p, "screenshot", "keep", "filename referenced in a project")
        else: add(p, "screenshot", "trash", "screenshot not referenced in scanned projects")
    gdir = X(ic["generated_dir"])
    if os.path.isdir(gdir) and not args.no_images:
        for r, ds, fs in os.walk(gdir):
            for f in fs:
                p = os.path.join(r, f)
                if not f.lower().endswith(exts): continue
                try: sz = os.path.getsize(p)
                except OSError: continue
                copy = None
                for q in proj_img_sizes.get(sz, []):
                    try:
                        if sha256(q) == sha256(p): copy = q; break
                    except OSError: pass
                if copy: add(p, "image_generated", "trash", "imagegen output; identical copy in project", copy=short(copy))
                elif image_refs(p, all_tokens): add(p, "image_generated", "keep", "filename referenced in a project")
                else: add(p, "image_generated", "trash", "imagegen output not used in any scanned project")

    dirs = sorted({os.path.expanduser(i["path"]) for i in items if os.path.isdir(os.path.expanduser(i["path"]))})
    def nested(i):
        p = os.path.expanduser(i["path"])
        return any(p != d and p.startswith(d.rstrip("/") + "/") for d in dirs)
    items[:] = [i for i in items if not nested(i)]
    # summary
    cats = {}
    for it in items:
        c = cats.setdefault(it["category"], {})
        a = c.setdefault(it["action"], {"count": 0, "bytes": 0})
        a["count"] += 1; a["bytes"] += it["size"]
    act = [it for it in items if it["action"] in ("trash", "archive_then_trash")]
    pid = hashlib.sha256(json.dumps(sorted((i["path"], i["size"], i["fingerprint"]["identity_sha256"], i["policy_revision"]) for i in act)).encode()).hexdigest()[:16]
    total = sum(i["size"] for i in act)
    out = {"plan_id": pid, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "min_age_days": cfg.get("min_age_days", 14),
           "projects_scanned": [short(p) for p in projects], "summary": cats,
           "actionable": {"count": len(act), "bytes": total},
           "limits_exceeded": total > cfg.get("max_plan_bytes", 5e9) or len(act) > cfg.get("max_plan_items", 200),
           "tools": tool_status(cfg), "items": items}
    sd = X(cfg.get("state_dir", "~/.codex/maintenance")); os.makedirs(sd, exist_ok=True)
    fn = os.path.join(sd, f"cleanup-plan-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}.json")
    atomic_record(fn, out)
    log(cfg, {"stage": "plan", "plan_id": pid, "file": short(fn), "actionable": out["actionable"]})
    return fn, out

def tool(name):
    """Resolve a CLI even when PATH lacks Homebrew (agents often run with a minimal PATH)."""
    return shutil.which(name) or next((c for c in (f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}") if os.access(c, os.X_OK)), None)

def tool_status(cfg):
    st = {t: bool(tool(t)) for t in ("age", "gitleaks", "gh", "zstd")}
    r = run([tool("gh"), "auth", "status"]) if st["gh"] else None
    st["gh_auth"] = bool(r and r.returncode == 0)
    st["repo_configured"] = bool(cfg["archive"].get("repo"))
    st["recipient_configured"] = bool(cfg["archive"].get("age_recipient"))
    return st

def log(cfg, rec):
    sd = X(cfg.get("state_dir", "~/.codex/maintenance")); os.makedirs(sd, exist_ok=True)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **rec}
    open(os.path.join(sd, "cleanup.jsonl"), "a").write(json.dumps(rec, ensure_ascii=False) + "\n")

# ---------- archive / verify / delete ----------
def load_plan(fn):
    return json.load(open(os.path.expanduser(fn)))

# ---------- encrypted GitHub archive (shared by archive + backup stages) ----------
def remote_paths(cfg, aid):
    pre = cfg["archive"].get("path_prefix", "").strip("/")
    base = "/".join(x for x in (pre, time.strftime("%Y"), time.strftime("%m")) if x)
    return f"{base}/{aid}.tar.zst.age", f"{base}/{aid}.manifest.json"

def gh_put(repo, rpath, data, msg, work):
    fn = os.path.join(work, "put.json")
    json.dump({"message": msg, "content": base64.b64encode(data).decode()}, open(fn, "w"))
    r = run([tool("gh"), "api", "-X", "PUT", f"repos/{repo}/contents/{rpath}", "--input", fn])
    os.remove(fn)
    return (r is not None and r.returncode == 0), (r.stderr.strip()[:300] if r else "gh missing")

def gh_get(repo, rpath):
    try:
        r = subprocess.run([tool("gh"), "api", f"repos/{repo}/contents/{rpath}", "-H", "Accept: application/vnd.github.raw"],
                           capture_output=True, timeout=600)
    except Exception: return None
    return r.stdout if r.returncode == 0 else None

def key_path(cfg): return X(cfg["archive"].get("identity_file", "~/.config/age/ai-backups.key"))

def archive_member_name(path):
    """Use the same normalized member name when packing and recording verification input."""
    path = os.path.abspath(os.path.expanduser(path))
    return os.path.relpath(path, HOME) if path.startswith(HOME + "/") else path.lstrip("/")

def decrypt_list(cfg, data):
    """Decrypt in memory/pipes (no plaintext on disk) and return the tar member names, or None if no key / failure."""
    key = key_path(cfg)
    if not os.path.exists(key): return None
    age = subprocess.Popen([tool("age"), "-d", "-i", key], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    zs = subprocess.Popen([tool("zstd"), "-d", "-q", "-c"], stdin=age.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    age.stdout.close()
    import threading
    t = threading.Thread(target=lambda: (age.stdin.write(data), age.stdin.close())); t.start()
    try:
        with tarfile.open(fileobj=zs.stdout, mode="r|") as tf: names = [m.name for m in tf]
    except tarfile.TarError: names = None
    t.join(); zs.stdout.close()
    return names if age.wait() == 0 and zs.wait() == 0 else None

def encrypt_upload(cfg, aid, paths, meta):
    """tar | zstd | age (streamed: no plaintext archive on disk), gitleaks-scan the manifest, upload both to the
    private repo, re-download and compare sha256, decrypt-list round-trip. Leaves no local copy (temp dir removed)."""
    st = tool_status(cfg); missing = [k for k, v in st.items() if not v]
    if missing: return {"ok": False, "refused": "archive prerequisites missing", "missing": missing}
    repo, rcp = cfg["archive"]["repo"], cfg["archive"]["age_recipient"]
    files = []
    for p in paths:
        a = os.path.abspath(os.path.expanduser(p))
        if not os.path.lexists(a): return {"ok": False, "error": f"missing: {short(a)}"}
        if os.path.isdir(a) and not os.path.islink(a):
            for r, ds, fs in os.walk(a):
                files += [os.path.join(r, f) for f in fs]
        else: files.append(a)
    if not files: return {"ok": False, "error": "nothing to back up"}
    total = sum(os.lstat(f).st_size for f in files)
    if total > cfg["archive"].get("max_input_bytes", 200_000_000):
        return {"ok": False, "refused": f"input {total} bytes exceeds [archive] max_input_bytes"}
    members = [archive_member_name(f) for f in files]
    work = tempfile.mkdtemp(prefix="ai-cleanup-")
    try:
        enc = os.path.join(work, "a.age")
        with open(enc, "wb") as out:
            age = subprocess.Popen([tool("age"), "-r", rcp], stdin=subprocess.PIPE, stdout=out)
            zs = subprocess.Popen([tool("zstd"), "-q", "-19", "-T0", "-c"], stdin=subprocess.PIPE, stdout=age.stdin)
            age.stdin.close()
            with tarfile.open(fileobj=zs.stdin, mode="w|") as tf:
                for f, member in zip(files, members): tf.add(f, arcname=member, recursive=False)
            zs.stdin.close(); zrc = zs.wait(); arc_rc = age.wait()
        if zrc or arc_rc: return {"ok": False, "error": f"zstd/age failed ({zrc}/{arc_rc})"}
        data = open(enc, "rb").read(); digest = hashlib.sha256(data).hexdigest()
        if len(data) > 50_000_000: return {"ok": False, "refused": "encrypted archive >50MB (GitHub contents API)"}
        rarc, rman = remote_paths(cfg, aid)
        manifest = {"id": aid, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "host": os.uname().nodename, **meta,
                    "format": "tar | zstd | age", "archive": rarc, "archive_sha256": digest, "archive_bytes": len(data),
                    "files": [{"path": short(f), "arcname": member, "size": os.lstat(f).st_size, "mtime": int(os.lstat(f).st_mtime),
                               "sha256": sha256(f) if os.path.isfile(f) and not os.path.islink(f) else None} for f, member in zip(files, members)]}
        mdir = os.path.join(work, "m"); os.makedirs(mdir)
        mbytes = (json.dumps(manifest, ensure_ascii=False, indent=1) + "\n").encode()
        open(os.path.join(mdir, "manifest.json"), "wb").write(mbytes)
        rep = os.path.join(work, "gitleaks.json")
        g = run([tool("gitleaks"), "dir", mdir, "--no-banner", "--report-format", "json", "--report-path", rep, "--exit-code", "0"])
        if not g or g.returncode != 0: return {"ok": False, "error": "gitleaks failed", "detail": (g.stderr[-300:] if g else "")}
        findings = json.load(open(rep)) if os.path.exists(rep) and os.path.getsize(rep) else []
        if findings: return {"ok": False, "refused": "manifest contains secret-like strings", "findings": len(findings)}
        for rpath, body in ((rarc, data), (rman, mbytes)):
            ok, err = gh_put(repo, rpath, body, f"ai-cleanup {aid} {os.path.basename(rpath)}", work)
            if not ok: return {"ok": False, "error": f"upload failed: {rpath}", "detail": err}
        back = gh_get(repo, rarc)
        sha_ok = back is not None and hashlib.sha256(back).hexdigest() == digest
        names = decrypt_list(cfg, back) if sha_ok else None
        rt_ok = names is not None and sorted(names) == sorted(members)
        return {"ok": bool(sha_ok and rt_ok), "id": aid, "repo": repo, "path": rarc, "manifest": rman, "sha256": digest, "bytes": len(data),
                "files": len(files), "input_bytes": total, "verified": sha_ok, "decrypt_roundtrip": rt_ok,
                "archive_members": members,
                "verified_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    finally:
        shutil.rmtree(work, ignore_errors=True)

def archive(cfg, args):
    p = load_plan(args.plan); pid = p["plan_id"]
    items = [i for i in p["items"] if i["action"] == "archive_then_trash"]
    if not items: print(json.dumps({"ok": True, "note": "nothing to archive"})); return 0
    rec = encrypt_upload(cfg, pid, [i["path"] for i in items],
                         {"kind": "archive", "plan_id": pid, "reason": "older AI-made config backups, archived before trash"})
    if not rec.get("ok"): print(json.dumps(rec)); return 4
    rec["items"] = [i["path"] for i in items]; rec["plan_id"] = pid
    json.dump(rec, open(os.path.join(X(cfg["state_dir"]), f"archive-{pid}.json"), "w"), indent=1)
    log(cfg, {"stage": "archive", **{k: rec[k] for k in ("plan_id", "repo", "path", "sha256", "files", "verified", "decrypt_roundtrip")}})
    print(json.dumps({k: v for k, v in rec.items() if k != "items"})); return 0

def verify(cfg, args):
    p = load_plan(args.plan); sd = X(cfg["state_dir"]); fn = os.path.join(sd, f"archive-{p['plan_id']}.json")
    if not os.path.exists(fn): print(json.dumps({"ok": False, "error": "no archive record"})); return 3
    rec = json.load(open(fn))
    members = rec.get("archive_members")
    if not isinstance(members, list) or not members or any(not isinstance(member, str) for member in members):
        print(json.dumps({"ok": False, "error": "archive lacks recorded member names; preserve this legacy record and recreate a verified archive from approved originals"})); return 4
    data = gh_get(rec["repo"], rec["path"])
    if data is None: print(json.dumps({"ok": False, "error": "download failed"})); return 4
    ok = hashlib.sha256(data).hexdigest() == rec["sha256"]
    names = decrypt_list(cfg, data) if ok else None
    rt = names is not None and sorted(names) == sorted(members)
    rec["verified"] = bool(ok and rt); rec["decrypt_roundtrip"] = rt; rec["verified_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    json.dump(rec, open(fn, "w"), indent=1); log(cfg, {"stage": "verify", "plan_id": p["plan_id"], "ok": rec["verified"], "decrypt_roundtrip": rt})
    print(json.dumps({"ok": rec["verified"], "sha256_match": ok, "decrypt_roundtrip": rt, "members": len(names or [])}))
    return 0 if rec["verified"] else 5

def backup(cfg, args):
    if not args.path or not args.reason: print("--path and --reason are required for --stage backup"); return 2
    aid = "bk-" + time.strftime("%Y%m%d-%H%M%S") + "-" + hashlib.sha256("|".join(args.path).encode()).hexdigest()[:6]
    rec = encrypt_upload(cfg, aid, args.path, {"kind": "backup", "reason": args.reason})
    if rec.get("ok"): log(cfg, {"stage": "backup", "reason": args.reason, **{k: rec[k] for k in ("id", "repo", "path", "sha256", "files", "decrypt_roundtrip")}})
    if rec.get("ok"):
        rec["restore"] = (f"gh api repos/{rec['repo']}/contents/{rec['path']} -H 'Accept: application/vnd.github.raw' | "
                          f"age -d -i ~/.config/age/ai-backups.key | zstd -d | tar -xf - -C <scratch dir>")
    print(json.dumps(rec, ensure_ascii=False)); return 0 if rec.get("ok") else 4

def check_item(cfg, it, archived=None):
    """Return a skip reason, or None if the item may be moved now."""
    path = os.path.expanduser(it["path"])
    guarded = protection_reason(cfg, path)
    if guarded: return guarded
    if not it.get("fingerprint") or it["fingerprint"].get("schema") != 2:
        return "legacy/unverified source snapshot; replan"
    try:
        if protection(cfg).revision() != it.get("policy_revision"): return "protection changed; replan"
        current = snapshot(path)
    except (OSError, SafetyError) as error: return "source unavailable: " + str(error)
    if current != it["fingerprint"]: return "source identity/content/tree changed since plan"
    if time.time() * 1e9 - current["newest_mtime_ns"] < cfg.get("min_age_days", 14) * 86400 * 1e9: return "too new"
    _ROOT_CACHE.clear(); _TRACKED_CACHE.clear()
    if is_tracked(path): return "git-tracked"
    if "protected" in it.get("reason", ""): return "protected"
    if it["action"] == "archive_then_trash" and not (archived and archived.get("verified") and archived.get("decrypt_roundtrip") is True and it["path"] in archived.get("items", [])):
        return "archive not verified"
    if it.get("copy"):
        try:
            if not os.path.isfile(X(it["copy"])) or sha256(X(it["copy"])) != sha256(path): return "retained copy changed or missing"
        except OSError: return "retained copy unavailable"
    return None

def move_items(cfg, items, dest, archived=None):
    moved, skipped = [], []
    dest = X(dest)
    for it in items:
        if under(dest, [X(it["path"])]) or under(X(it["path"]), [dest]):
            raise SafetyError("Trash destination overlaps a source")
    with journal_lock(dest):
        rpath = os.path.join(dest, "restore.json")
        if os.path.islink(rpath): raise SafetyError("linked restore journal")
        rec = json.load(open(rpath)) if os.path.exists(rpath) else {"schema": 2, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "items": []}
        for it in items:
            why = check_item(cfg, it, archived)
            if why: skipped.append({"path": it["path"], "why": why}); continue
            path = X(it["path"])
            entry_dir = os.path.join(dest, "files", uuid.uuid4().hex)
            os.makedirs(entry_dir, mode=0o700, exist_ok=False)
            target = os.path.join(entry_dir, "payload")
            entry = {"move_id": uuid.uuid4().hex, "from": short(path), "to": short(target), "size": it["size"],
                     "category": it["category"], "fingerprint": it["fingerprint"]}
            rec["items"].append(entry)
            def verify():
                observed = snapshot(target)
                if not same_moved_object(it["fingerprint"], observed): raise SafetyError("post-move identity/content mismatch")
                entry["moved_fingerprint"] = observed
            done = recorded_transfer(rec, entry, lambda data: atomic_record(rpath, data),
                                     lambda: check_item(cfg, it, archived),
                                     lambda: rename_exclusive(path, target, it["fingerprint"]), verify)
            if done: moved.append(it)
            else: skipped.append({"path": it["path"], "why": entry.get("reason", "held")})
    return moved, skipped

def delete(cfg, args):
    p = load_plan(args.plan); pid = p["plan_id"]
    if args.confirm != pid:
        print(json.dumps({"ok": False, "refused": "explicit user confirmation required: --confirm " + pid})); return 3
    cand = [it for it in p["items"] if it["action"] in ("trash", "archive_then_trash")
            and (not args.only_category or it["category"] in args.only_category)]
    big = sum(it["size"] for it in cand) > cfg.get("max_plan_bytes", 5e9) or len(cand) > cfg.get("max_plan_items", 200)
    if big and not args.allow_large:
        print(json.dumps({"ok": False, "refused": "selection exceeds size/item limits; narrow with --only-category or pass --allow-large after asking"})); return 3
    sd = X(cfg["state_dir"]); arec = os.path.join(sd, f"archive-{pid}.json")
    archived = json.load(open(arec)) if os.path.exists(arec) else {}
    todo, skipped = [], []
    for it in cand:
        why = check_item(cfg, it, archived)
        (skipped.append({"path": it["path"], "why": why}) if why else todo.append(it))
    troot, tnote = trash_root(cfg); dest = os.path.join(troot, f"ai-cleanup-{pid}")
    moved, sk2 = move_items(cfg, todo, dest, archived); skipped += sk2
    log(cfg, {"stage": "delete", "plan_id": pid, "only_category": args.only_category, "moved": len(moved), "skipped": len(skipped), "trash": short(dest)})
    print(json.dumps({"ok": True, "moved": len(moved), "skipped": skipped[:50], "trash": short(dest)}, ensure_ascii=False))
    return 0

# ---------- auto tier ----------
def auto_tier(cfg, it):
    """Central automatic scope cannot be widened by candidate globs or labels."""
    if it["action"] != "trash": return False
    a = cfg.get("auto", {})
    cap_dirs = {d.lower() for d in a.get("capture_dir_names", ["tmp", "output", "artifacts"])} & {"tmp", "output", "artifacts"}
    c, path = it["category"], X(it["path"])
    tmp_root = X("/private/tmp")
    in_tmp = path != tmp_root and under(path, [tmp_root])
    if c in ("build_artifact", "scratch"): return in_tmp
    if c == "test_output":
        return in_tmp or (os.path.dirname(path) == X(HOME) and fnmatch.fnmatchcase(os.path.basename(path), "api-spec-test-*"))
    if c == "image_generated":
        generated = X(os.path.join(os.environ.get("CODEX_HOME", os.path.join(HOME, ".codex")), "generated_images"))
        return path != generated and under(path, [generated])
    if c == "screenshot":
        desktop = X(os.path.join(HOME, "Desktop"))
        return in_tmp or (path != desktop and under(path, [desktop]))
    if c in ("image_project_untracked", "image_large") and it.get("project"):
        project = X(it["project"])
        if path == project or not under(path, [project]): return False
        rel = os.path.relpath(path, project).lower().split("/")[:-1]
        return any(seg in cap_dirs for seg in rel)
    return False

def last_auto_run(cfg):
    fn = os.path.join(X(cfg.get("state_dir", "~/.codex/maintenance")), "cleanup.jsonl"); last = None
    if os.path.exists(fn):
        for line in open(fn):
            try: r = json.loads(line)
            except ValueError: continue
            if r.get("stage") == "auto" and not r.get("dry_run"):
                last = r.get("ts")
    return last

def old_trash_candidates(cfg):
    """Inventory only. Permanent deletion is not an operation of this script."""
    days = cfg.get("trash", {}).get("report_age_days", cfg.get("auto", {}).get("trash_retention_days", 7)); out = []
    roots = {X(cfg.get("trash_dir", "~/.Trash")), X(cfg.get("trash_fallback_dir", "~/.codex/maintenance/trash"))}
    for d in [g for r in roots for g in glob.glob(os.path.join(r, "ai-cleanup-*"))]:
        rp = os.path.join(d, "restore.json")
        try: ref = os.path.getmtime(rp) if os.path.exists(rp) else os.path.getmtime(d)
        except OSError: continue
        if time.time() - ref >= days * 86400:
            out.append({"path": short(d), "size": size_of(d)})
    return out

def auto(cfg, args):
    a = cfg.get("auto", {}); dry = args.dry_run
    last = last_auto_run(cfg)
    if last and not args.force and not dry:
        try:
            if NOW - time.mktime(time.strptime(last[:19], "%Y-%m-%dT%H:%M:%S")) < a.get("min_interval_hours", 24) * 3600:
                print(json.dumps({"ok": True, "skipped": "throttled", "last_run": last})); return 0
        except ValueError: pass
    fn, plan_out = plan(cfg, args)
    cand = [it for it in plan_out["items"] if auto_tier(cfg, it)]
    cand.sort(key=lambda i: -i["age_days"])  # oldest first
    eligible, skipped = [], []
    for it in cand:
        why = check_item(cfg, it)
        (skipped.append({"path": it["path"], "why": why}) if why else eligible.append(it))
    max_bytes = a.get("max_bytes_per_run", 5_000_000_000); batch_n = a.get("batch_items", 200); max_batches = a.get("max_batches_per_run", 25)
    run_items, total, deferred = [], 0, 0
    for it in eligible:
        if total + it["size"] > max_bytes or len(run_items) >= batch_n * max_batches: deferred += 1; continue
        run_items.append(it); total += it["size"]
    batches = [run_items[i:i + batch_n] for i in range(0, len(run_items), batch_n)]
    rid = plan_out["plan_id"]; troot, tnote = trash_root(cfg); dest = os.path.join(troot, f"ai-cleanup-{rid}")
    moved = []
    if not dry:
        for bt in batches:
            mv, sk = move_items(cfg, bt, dest); moved += mv; skipped += sk
    old_trash = old_trash_candidates(cfg)
    by_cat = {}
    for it in (run_items if dry else moved):
        c = by_cat.setdefault(it["category"], {"count": 0, "bytes": 0}); c["count"] += 1; c["bytes"] += it["size"]
    confirm = [it for it in plan_out["items"] if it["action"] in ("needs_user_confirm", "archive_then_trash")
               or (it["action"] == "trash" and not auto_tier(cfg, it))]
    conf = {}
    for it in confirm:
        c = conf.setdefault(it["category"], {"count": 0, "bytes": 0}); c["count"] += 1; c["bytes"] += it["size"]
    n = len(run_items) if dry else len(moved); b = sum(i["size"] for i in (run_items if dry else moved))
    summary = (f"ai-cleanup {'DRY-RUN would move' if dry else 'moved'} {n} items ({b/1e9:.2f} GB) in {len(batches)} batch(es) "
               f"to {short(dest)}; deferred {deferred}; skipped {len(skipped)}; confirm-tier {len(confirm)} items "
               f"({sum(i['size'] for i in confirm)/1e9:.2f} GB) need the user; old managed trash reported {len(old_trash)}, never emptied"
               + (f"; NOTE {tnote}" if tnote else "")
               + ("" if dry else f"; restore: python3 {short(os.path.abspath(__file__))} --stage restore --id {rid}"))
    log(cfg, {"stage": "auto", "dry_run": dry, "plan_id": rid, "moved": 0 if dry else len(moved), "bytes": b,
              "deferred": deferred, "skipped": len(skipped), "trash": short(dest), "emptied": 0, "old_trash_candidates": len(old_trash)})
    print(json.dumps({"ok": True, "dry_run": dry, "summary": summary, "plan_file": short(fn), "auto_by_category": by_cat,
                      "confirm_tier_by_category": conf, "skipped_sample": skipped[:20], "emptied": [],
                      "old_trash_candidates": old_trash, "permanent_deletion_performed": False},
                     ensure_ascii=False, indent=1))
    return 0

def restore(cfg, args):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", args.id):
        print(json.dumps({"ok": False, "error": "invalid restore id"})); return 3
    rp = None
    for r in (X(cfg.get("trash_dir", "~/.Trash")), X(cfg.get("trash_fallback_dir", "~/.codex/maintenance/trash"))):
        cand = os.path.join(r, f"ai-cleanup-{args.id}", "restore.json")
        try:
            if os.path.exists(cand): rp = cand; break
        except OSError: pass
    rp = rp or "/nonexistent"
    if not os.path.exists(rp): print(json.dumps({"ok": False, "error": "no restore.json for " + args.id})); return 3
    back, skipped = 0, []
    managed = X(os.path.dirname(rp)); files_root = X(os.path.join(managed, "files"))
    with journal_lock(managed):
        if os.path.islink(rp): raise SafetyError("linked restore journal")
        rec = json.load(open(rp))
        if not isinstance(rec.get("items"), list): raise SafetyError("invalid restore journal")
        for it in rec["items"]:
            src, to = X(it["to"]), X(it["from"])
            if not under(src, [files_root]) or to in ("/", HOME):
                skipped.append({"path": it["from"], "why": "unsafe restore mapping"}); continue
            source = snapshot(to, allow_recovery=True) if os.path.lexists(to) else None
            trashed = snapshot(src, allow_recovery=True) if os.path.lexists(src) else None
            state = restoration_state(it, source, trashed)
            if state != "ready": skipped.append({"path": it["from"], "why": state}); continue
            parent = os.path.dirname(to)
            if it.get("fingerprint"):
                if not os.path.isdir(parent) or [os.stat(parent).st_dev, os.stat(parent).st_ino] != it["fingerprint"]["parent"]:
                    skipped.append({"path": it["from"], "why": "original parent changed; manual reconciliation required"}); continue
            else:
                # Legacy journals remain restorable, without inventing old identity evidence.
                os.makedirs(parent, exist_ok=True)
                it["legacy_identity_evidence"] = "unavailable; current Trash object bound for this restore"
            def recheck():
                if os.path.lexists(to): return "original path appeared; never overwrite"
                current = snapshot(src, allow_recovery=True)
                if current != trashed: return "Trash object changed before restore"
                if it.get("fingerprint") and [os.stat(parent).st_dev, os.stat(parent).st_ino] != it["fingerprint"]["parent"]:
                    return "original parent changed before restore"
                return None
            def verify():
                observed = snapshot(to, allow_recovery=True)
                if not same_moved_object(trashed, observed): raise SafetyError("restored object verification failed")
                it["restored_fingerprint"] = observed
            if recorded_transfer(rec, it, lambda data: atomic_record(rp, data), recheck,
                                 lambda: rename_exclusive(src, to, trashed), verify, restoring=True): back += 1
            else: skipped.append({"path": it["from"], "why": it.get("reason", "restore held at final recheck")})
    unresolved = [item for item in skipped if item["why"] != "at_original"]
    log(cfg, {"stage": "restore", "id": args.id, "restored": back, "skipped": len(skipped), "unresolved": len(unresolved)})
    print(json.dumps({"ok": not unresolved, "restored": back, "skipped": skipped[:50], "unresolved": len(unresolved)}, ensure_ascii=False))
    return 4 if unresolved else 0

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["plan", "archive", "verify", "delete", "restore", "backup"], default="plan")
    ap.add_argument("--path", nargs="+", help="with --stage backup: files/folders to back up (encrypted, to the GitHub repo)")
    ap.add_argument("--reason", help="with --stage backup: why (e.g. 'before replacing signing config')")
    ap.add_argument("--only-category", nargs="+", help="with --stage delete: only move items of these categories (e.g. backup)")
    ap.add_argument("--auto", action="store_true", help="plan + move only the auto tier (older than min_age, batched, throttled to once per interval)")
    ap.add_argument("--dry-run", action="store_true", help="with --auto: report what would move; move nothing")
    ap.add_argument("--force", action="store_true", help="with --auto: ignore the once-per-day throttle")
    ap.add_argument("--id", help="with --stage restore: the ai-cleanup id (trash folder suffix)")
    ap.add_argument("--config", default=os.path.join(HERE, "cleanup.toml"))
    ap.add_argument("--plan"); ap.add_argument("--confirm"); ap.add_argument("--allow-large", action="store_true")
    ap.add_argument("--no-images", action="store_true", help="skip project/generated image scan")
    args = ap.parse_args()
    cfg = tomllib.load(open(args.config, "rb"))
    if args.auto:
        return auto(cfg, args)
    if args.stage == "backup":
        return backup(cfg, args)
    if args.stage == "restore":
        if not args.id: print("--id is required for restore"); return 2
        return restore(cfg, args)
    if args.stage != "plan" and not args.plan:
        print("--plan FILE is required for this stage"); return 2
    if args.stage == "plan":
        fn, out = plan(cfg, args)
        print(json.dumps({"plan_file": short(fn), "plan_id": out["plan_id"], "actionable": out["actionable"],
                          "limits_exceeded": out["limits_exceeded"], "tools": out["tools"],
                          "projects_scanned": len(out["projects_scanned"]), "summary": out["summary"]}, ensure_ascii=False, indent=1))
        return 0
    return {"archive": archive, "verify": verify, "delete": delete}[args.stage](cfg, args)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (SafetyError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error), "action": "stopped; inspect durable journal before retry"}, ensure_ascii=False))
        sys.exit(4)
