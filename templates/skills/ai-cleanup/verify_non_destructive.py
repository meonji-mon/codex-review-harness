#!/usr/bin/env python3
"""Run cleanup regressions without real transfers, deletion, or journal writes."""
import ctypes
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True

# Exactly the read-only query used by cleanup_safety.SharedProtection.reason.
PROTECTION_QUERY = ('source "$1"\nshift\npolicy_home="$1"\nshift\n'
                    'load_mole_whitelist "$policy_home"\n'
                    'count="$1"\nshift\n'
                    'for ((i=0;i<count;i++)); do WHITELIST_PATTERNS+=("$1"); shift; done\n'
                    'for candidate in "$@"; do '
                    'if is_path_whitelisted "$candidate"; then printf "1\\n"; else printf "0\\n"; fi; done\n')
FORBIDDEN = {"os.remove", "os.rmdir", "os.rename", "os.mkdir", "os.chmod", "os.chown",
             "os.truncate", "os.link", "os.symlink", "os.utime", "os.system",
             "os.posix_spawn", "os.exec", "os.fork", "shutil.rmtree", "shutil.copyfile",
             "shutil.copytree", "ctypes.dlopen", "ctypes.dlsym"}
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


def audit(event, args):
    if event in FORBIDDEN:
        raise PermissionError("non-destructive verification forbids " + event)
    if event == "open" and args[2] & WRITE_FLAGS:
        raise PermissionError("non-destructive verification forbids file writes")
    if event == "subprocess.Popen":
        executable, argv = args[:2]
        allowed = (executable == "/bin/bash" and isinstance(argv, (list, tuple)) and len(argv) >= 8
                   and argv[:4] == ["/bin/bash", "-c", PROTECTION_QUERY, "shared-cleanup-protection"]
                   and str(argv[4]).endswith("/lib/core/app_protection.sh"))
        if not allowed:
            raise PermissionError("non-destructive verification permits only Mole protection queries")


if __name__ == "__main__":
    sys.addaudithook(audit)
    with patch.object(ctypes, "CDLL", side_effect=PermissionError("native move calls are forbidden")):
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern="test_cleanup_safety.py")
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
