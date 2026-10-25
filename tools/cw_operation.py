#!/usr/bin/env python3
"""
Read a Cloudways operation response on stdin, print "<is_completed>|<status> <message>".

The release workflow queues a git pull and gets back only an operation id, so it polls
this endpoint to find out whether the pull actually ran. Keeping the parsing here rather
than inline in the workflow means it can be tested, and a malformed response prints a
usable line instead of breaking the shell.
"""
import json
import sys


def main():
    try:
        op = (json.load(sys.stdin) or {}).get("operation") or {}
    except (json.JSONDecodeError, ValueError):
        print("|unreadable response")
        return
    done = str(op.get("is_completed", "")).strip()
    status = str(op.get("status", "") or "").strip()
    message = str(op.get("message", "") or "").strip()[:160]
    print(f"{done}|{status} {message}".rstrip())


if __name__ == "__main__":
    main()
