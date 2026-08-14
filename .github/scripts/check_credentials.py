#!/usr/bin/env python3
"""Fail if a tracked file looks like it carries a real credential.

Named "credentials" and not "secrets" on purpose: .gitignore ignores *secret* on sight.

The recipes in this repository walk through device credentials, so the words
"local_key" and "device id" appear all over the text. This check therefore looks for
credential *values* — an assignment, an id-shaped token, a MAC address — and not for
the words themselves.

Run it the way CI does:

    python3 .github/scripts/check_credentials.py
"""

import re
import subprocess
import sys

# Files that hold real keys. They are in .gitignore; this catches `git add -f`.
FORBIDDEN_NAMES = {
    "devices.json",
    "tinytuya.json",
    "snapshot.json",
    "tuya-raw.json",
}

SKIP_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".pdf", ".ico", ".woff", ".woff2")

# A screenshot can leak just as much as a text file, but nothing here can read one.
# Reviewers check images by eye — see CONTRIBUTING.
MAX_IMAGE_BYTES = 1_000_000

PATTERNS = [
    (
        "Tuya local_key assigned a value",
        re.compile(r"local_?key[\"']?\s*[:=]\s*[\"'][^\"']{6,}[\"']", re.I),
    ),
    (
        "Tuya device id",
        re.compile(r"\bbf[0-9a-z]{18,24}\b"),
    ),
    (
        "Tuya cloud credential assigned a value",
        re.compile(
            r"(access_?(id|secret)|client_?secret|api_?key)[\"']?\s*[:=]\s*[\"'][^\"']{6,}[\"']",
            re.I,
        ),
    ),
    (
        "MAC address",
        re.compile(r"\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b", re.I),
    ),
    (
        "home coordinates from a Tuya dump",
        re.compile(r"\"(lat|lon)\"\s*:\s*\"?-?\d{1,3}\.\d{3,}"),
    ),
    (
        "account identifier from a Tuya dump",
        re.compile(r"\"(owner_id|uid|terminal_id)\"\s*:"),
    ),
    (
        "e-mail address",
        re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.I),
    ),
]

# Placeholders the articles use on purpose.
ALLOWED = re.compile(
    r"(<LOCAL_KEY>|<DEVICE_ID>|xxxx|XXXX|example\.(com|org|net)|"
    r"contributor-covenant|noreply@github\.com)",
)


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files", "-z"], capture_output=True, text=True, check=True
    ).stdout
    return [name for name in out.split("\0") if name]


def main():
    problems = []

    for name in tracked_files():
        if name.rsplit("/", 1)[-1] in FORBIDDEN_NAMES:
            problems.append(f"{name}: this file holds real device keys and must never be committed")
            continue

        if name.lower().endswith(SKIP_SUFFIXES):
            try:
                with open(name, "rb") as fh:
                    size = len(fh.read())
            except OSError as exc:
                problems.append(f"{name}: cannot read ({exc})")
                continue
            if size > MAX_IMAGE_BYTES:
                problems.append(f"{name}: {size // 1024} KB — shrink it, the limit is 1 MB")
            continue

        try:
            with open(name, encoding="utf-8") as fh:
                lines = fh.readlines()
        except (OSError, UnicodeDecodeError):
            continue

        for number, line in enumerate(lines, start=1):
            if ALLOWED.search(line):
                continue
            for label, pattern in PATTERNS:
                found = pattern.search(line)
                if found:
                    problems.append(f"{name}:{number}: {label} — {found.group(0)[:40]}")

    if problems:
        print("Possible secrets found:\n")
        for problem in problems:
            print(f"  {problem}")
        print(
            "\nIf a hit is a false positive, add the placeholder form to ALLOWED in this script."
        )
        return 1

    print(f"No secrets found in {len(tracked_files())} tracked files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
