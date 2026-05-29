"""
Windows wrapper for run_loop.py.
Patches subprocess to use claude.cmd full path since Python subprocess
on Windows cannot find .cmd files without shell=True.
"""
import subprocess
import sys
import os
from pathlib import Path

CLAUDE_CMD = r"C:\Users\Administrator\AppData\Roaming\npm\claude.cmd"

# Monkey-patch Popen
_orig_popen_init = subprocess.Popen.__init__

def _patched_popen_init(self, args, **kwargs):
    if isinstance(args, list) and args and args[0] == "claude":
        args = [CLAUDE_CMD] + list(args[1:])
    elif isinstance(args, str) and args.startswith("claude "):
        args = CLAUDE_CMD + args[len("claude"):]
    return _orig_popen_init(self, args, **kwargs)

subprocess.Popen.__init__ = _patched_popen_init

# Monkey-patch run
_orig_run = subprocess.run

def _patched_run(args, **kwargs):
    if isinstance(args, list) and args and args[0] == "claude":
        args = [CLAUDE_CMD] + list(args[1:])
    return _orig_run(args, **kwargs)

subprocess.run = _patched_run

# Add skill-creator to path so scripts module is importable
SKILL_CREATOR = Path(r"C:\Users\Administrator\.claude\plugins\cache\claude-plugins-official\skill-creator\8435428dfc0f\skills\skill-creator")
sys.path.insert(0, str(SKILL_CREATOR))

# Import and run the loop
from scripts.run_loop import main
sys.argv = sys.argv  # keep args as-is
main()
