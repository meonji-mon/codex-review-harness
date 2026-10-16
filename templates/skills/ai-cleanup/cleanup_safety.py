"""Shared Mole protection, immutable source snapshots, and durable move records.

No cleanup runs on import. Permanent deletion is deliberately absent.
"""
import contextlib
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time
import uuid


class SafetyError(RuntimeError):
    pass


def canonical(path):
    return os.path.realpath(os.path.expanduser(os.fspath(path)))


def overlaps(path, root):
    path, root = canonical(path), canonical(root)
    if sys.platform == "darwin":
        path, root = path.casefold(), root.casefold()
    return path == root or path.startswith(root.rstrip("/") + "/") or root.startswith(path.rstrip("/") + "/")


def recovery_component(path):
    parts = tuple(p.casefold() for p in Path(path).parts)
    if any(p in {"localhistory", "graphify-out", ".git"} for p in parts):
        return True
    return any(pair in {(".idea", "shelf"), ("user", "history")} for pair in zip(parts, parts[1:]))


class SharedProtection:
    """Use Mole's installed matcher and persistent policy, not a second allowlist."""

    def __init__(self, cfg):
        self.home = os.path.expanduser("~")
        self.roots = [canonical(p) for p in cfg["never_touch"]["paths"]]
        executable = shutil.which("mo") or "/opt/homebrew/bin/mo"
        self.core = Path(executable).resolve().parent / "lib/core/app_protection.sh"
        self.policy = Path(self.home) / ".config/mole/whitelist"
        self.required = [os.path.expanduser(p) for p in cfg.get("protection", {}).get("required_mole_patterns", [])]
        self.cfg = cfg
        self.cache = {}

    def revision(self):
        try:
            data = self.policy.read_bytes()
            entries = {p.strip() for p in data.decode().splitlines() if p.strip() and not p.lstrip().startswith("#")}
            if any(p not in entries for p in self.required):
                raise SafetyError("shared IDE protection is missing; keep candidates and repair the Mole policy")
            digest = hashlib.sha256(data)
            for source in [self.core, self.core.with_name("base.sh"), self.core.with_name("app_protection_data.sh"),
                           Path(__file__), Path(__file__).with_name("ai_cleanup.py")]:
                digest.update(str(source).encode())
                digest.update(source.read_bytes())
            digest.update(json.dumps(self.roots, sort_keys=True).encode())
            digest.update(json.dumps({k: v for k, v in self.cfg.items() if not k.startswith("_")}, sort_keys=True).encode())
            return digest.hexdigest()
        except (OSError, UnicodeError, TypeError) as error:
            raise SafetyError("shared protection unavailable; no moves permitted") from error

    def reason(self, path):
        if recovery_component(path) or any(overlaps(path, root) for root in self.roots):
            return "protected recovery/state path or its ancestor"
        revision = self.revision()
        normalized = canonical(path)
        key = (revision, normalized)
        if key not in self.cache:
            script = ('source "$1"\nshift\npolicy_home="$1"\nshift\n'
                      'load_mole_whitelist "$policy_home"\n'
                      'count="$1"\nshift\n'
                      'for ((i=0;i<count;i++)); do WHITELIST_PATTERNS+=("$1"); shift; done\n'
                      'for candidate in "$@"; do '
                      'if is_path_whitelisted "$candidate"; then printf "1\\n"; else printf "0\\n"; fi; done\n')
            try:
                result = subprocess.run(["/bin/bash", "-c", script, "shared-cleanup-protection", str(self.core),
                                         self.home, str(len(self.roots)), *self.roots, os.path.abspath(os.path.expanduser(path)), normalized],
                                        capture_output=True, text=True, timeout=5)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise SafetyError("shared Mole protection could not be queried") from error
            answers = result.stdout.splitlines()
            if result.returncode or result.stderr or len(answers) != 2 or any(p not in {"0", "1"} for p in answers):
                raise SafetyError("invalid shared Mole protection result")
            if revision != self.revision():
                raise SafetyError("protection changed during the query; replan")
            self.cache[key] = "1" in answers
        return "Mole shared protected path or ancestor" if self.cache[key] else None


def snapshot(path, allow_recovery=False):
    """Hash content and nanosecond metadata; reject links, special files, and unstable reads."""
    path = os.path.abspath(os.path.expanduser(os.fspath(path)))
    if os.path.islink(path):
        raise SafetyError("symlink source")
    parent = canonical(os.path.dirname(path))
    ps = os.stat(parent)
    nodes, identity, content, newest, total, root = [path], [], [], 0, 0, None
    while nodes:
        item = nodes.pop()
        before = os.lstat(item)
        if before.st_uid != os.getuid() or not (stat.S_ISREG(before.st_mode) or stat.S_ISDIR(before.st_mode)):
            raise SafetyError("unowned, linked, or special source entry")
        if not allow_recovery and recovery_component(item):
            raise SafetyError("recovery/Git state inside candidate; keep its ancestor")
        relative = os.path.relpath(item, path)
        metadata = [before.st_dev, before.st_ino, before.st_mode, before.st_size,
                    before.st_mtime_ns, before.st_ctime_ns, before.st_nlink]
        newest = max(newest, before.st_mtime_ns)
        if root is None:
            root = metadata
        digest = None
        if stat.S_ISDIR(before.st_mode):
            with os.scandir(item) as entries:
                nodes.extend(sorted((entry.path for entry in entries), reverse=True))
        else:
            fd = os.open(item, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                opened = os.fstat(fd)
                if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                    raise SafetyError("source replaced while opening")
                h = hashlib.sha256()
                while True:
                    block = os.read(fd, 1 << 20)
                    if not block:
                        break
                    h.update(block)
                digest = h.hexdigest()
                after = os.fstat(fd)
            finally:
                os.close(fd)
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise SafetyError("file changed while hashing")
            total += before.st_size
        after = os.lstat(item)
        if metadata != [after.st_dev, after.st_ino, after.st_mode, after.st_size,
                        after.st_mtime_ns, after.st_ctime_ns, after.st_nlink]:
            raise SafetyError("entry changed while scanning")
        identity.append([relative, *metadata, digest])
        content.append([relative, stat.S_IFMT(before.st_mode), stat.S_IMODE(before.st_mode),
                        before.st_size if digest else None, digest])
    for relative, *saved in identity:
        current = os.lstat(path if relative == "." else os.path.join(path, relative))
        if saved[:-1] != [current.st_dev, current.st_ino, current.st_mode, current.st_size,
                          current.st_mtime_ns, current.st_ctime_ns, current.st_nlink]:
            raise SafetyError("tree changed after enumeration")
    # Include all entries, including empty directories. Rename changes root ctime,
    # so content/identity digests are separate for post-move recovery verification.
    encode = lambda rows: hashlib.sha256(json.dumps(sorted(rows), separators=(",", ":")).encode()).hexdigest()
    return {"schema": 2, "identity_sha256": encode(identity), "content_sha256": encode(content),
            "root": root, "parent": [ps.st_dev, ps.st_ino], "newest_mtime_ns": newest,
            "logical_bytes": total, "entry_count": len(identity)}


def same_moved_object(expected, observed):
    return expected["root"][:2] == observed["root"][:2] and expected["content_sha256"] == observed["content_sha256"]


def atomic_record(path, record):
    """Durably replace metadata. Failed pending records are retained, never unlinked."""
    path = Path(path)
    if path.is_symlink() or (path.exists() and path.stat().st_uid != os.getuid()):
        raise SafetyError("unsafe journal")
    parent_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        parent = os.fstat(parent_fd)
        if parent.st_uid != os.getuid() or parent.st_mode & 0o022:
            raise SafetyError("journal parent is not private to its owner")
        pending = path.name + ".pending-" + uuid.uuid4().hex
        fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent_fd)
        with os.fdopen(fd, "w") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=1)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(pending, path.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        os.fsync(parent_fd)
        current = os.stat(path.parent)
        if (current.st_dev, current.st_ino) != (parent.st_dev, parent.st_ino):
            raise SafetyError("journal parent changed during persistence")
    finally:
        os.close(parent_fd)


@contextlib.contextmanager
def journal_lock(directory):
    os.makedirs(directory, mode=0o700, exist_ok=True)
    if os.path.islink(directory) or os.stat(directory).st_uid != os.getuid() or os.stat(directory).st_mode & 0o022:
        raise SafetyError("unsafe journal directory")
    fd = os.open(os.path.join(directory, "move.lock"), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise SafetyError("another operation owns this move journal") from error
        yield
    finally:
        os.close(fd)


def rename_exclusive(source, target, expected):
    """Same-filesystem, no-overwrite rename bound to the checked parent/object."""
    if sys.platform != "darwin":
        raise SafetyError("exclusive rename is not verified on this platform")
    source, target = Path(source), Path(target)
    if source.parent.resolve() == target.parent.resolve() and source.name == target.name:
        raise SafetyError("identical source and destination")
    sf = os.open(source.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    tf = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        parent, dst_parent = os.fstat(sf), os.fstat(tf)
        current = os.stat(source.name, dir_fd=sf, follow_symlinks=False)
        actual = [current.st_dev, current.st_ino, current.st_mode, current.st_size,
                  current.st_mtime_ns, current.st_ctime_ns, current.st_nlink]
        if [parent.st_dev, parent.st_ino] != expected["parent"] or actual != expected["root"]:
            raise SafetyError("source identity changed immediately before rename")
        if current.st_dev != dst_parent.st_dev:
            raise SafetyError("cross-filesystem moves are refused; no copy-and-delete fallback")
        libc = ctypes.CDLL(None, use_errno=True)
        rename = libc.renameatx_np
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        # Installed Darwin SDK sys/stdio.h: RENAME_EXCL = 0x00000004.
        if rename(sf, os.fsencode(source.name), tf, os.fsencode(target.name), 4):
            number = ctypes.get_errno()
            raise OSError(number, os.strerror(number))
        os.fsync(tf)
        os.fsync(sf)
    finally:
        os.close(tf)
        os.close(sf)


def recorded_transfer(record, entry, persist, recheck, transfer, verify, restoring=False):
    """Persist intent before I/O, recheck at the boundary, then commit outcome.

    If a post-transfer record write fails, the durable intent still contains both
    locations and the expected content identity. Callers must stop, not claim PASS.
    """
    field = "restore_status" if restoring else "status"
    entry[field] = "intent"
    persist(record)  # Any failure here prevents transfer entirely.
    why = recheck()
    if why:
        entry[field] = "held"
        entry["reason"] = why
        persist(record)
        return False
    try:
        transfer()
        verify()
    except Exception as error:
        entry[field] = "attention"
        entry["reason"] = type(error).__name__ + ": " + str(error)
        persist(record)
        raise SafetyError("transfer requires reconciliation; see its durable journal") from error
    entry[field] = "restored" if restoring else "moved"
    persist(record)
    return True


def restoration_state(entry, source_snapshot, destination_snapshot):
    """Classify interrupted moves without changing either location."""
    if source_snapshot is not None and destination_snapshot is not None:
        return "conflict"
    if source_snapshot is None and destination_snapshot is None:
        return "missing"
    expected = entry.get("fingerprint")
    if destination_snapshot is not None:
        return "ready" if expected is None or same_moved_object(expected, destination_snapshot) else "changed"
    return "at_original" if expected is None or same_moved_object(expected, source_snapshot) else "changed"
