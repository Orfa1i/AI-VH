"""
Secret scanner for AI Virtual Hospital (AI-VH).
Scans files and commits for hardcoded credentials, API keys, private keys, and secrets.
Can be executed as a pre-commit hook, CI step, or standalone utility.
"""

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Pattern, Tuple


@dataclass
class Finding:
    file_path: str
    line_number: int
    rule_name: str
    snippet: str


RULES: List[Tuple[str, Pattern]] = [
    ("AWS Access Key ID", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
    ("GitHub Personal Access Token", re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{36,255})\b")),
    ("GitHub Fine-Grained Token", re.compile(r"\b(github_pat_[A-Za-z0-9_]{82})\b")),
    ("Slack API Token", re.compile(r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b")),
    ("Google API Key", re.compile(r"\b(AIza[0-9A-Za-z\-_]{35})\b")),
    ("OpenAI / Provider API Key", re.compile(r"\b(sk-[a-zA-Z0-9\-_]{32,64})\b")),
    ("Private Key Header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Generic High-Entropy Secret", re.compile(r"""(?i)(?:api_key|secret_key|private_key|auth_token)\s*=\s*['"]([A-Za-z0-9+/=_-]{32,})['"]""")),
]

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "MedGemma Model",
    "Medical Books",
    "models",
}

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf",
    ".safetensors", ".bin", ".pt", ".npy", ".pyc", ".db", ".sqlite", ".sqlite3"
}

ALLOWLIST_MARKERS = ("pragma: allowlist secret", "nosec", "gitleaks:allow")


def is_ignored(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORED_DIRS:
            return True
    if path.suffix.lower() in IGNORED_EXTENSIONS:
        return True
    return False


def scan_file(file_path: Path) -> List[Finding]:
    """Scan a single text file for credential patterns."""
    findings: List[Finding] = []
    if not file_path.is_file() or is_ignored(file_path):
        return findings

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                if any(marker in line for marker in ALLOWLIST_MARKERS):
                    continue
                for rule_name, pattern in RULES:
                    if pattern.search(line):
                        clean_snippet = line.strip()[:80]
                        findings.append(Finding(
                            file_path=str(file_path),
                            line_number=line_no,
                            rule_name=rule_name,
                            snippet=clean_snippet
                        ))
    except Exception as e:
        sys.stderr.write(f"Warning: Could not read {file_path}: {e}\n")

    return findings


def scan_directory(root_dir: Path) -> List[Finding]:
    """Recursively scan an entire directory for secrets."""
    all_findings: List[Finding] = []
    for root, dirs, files in os.walk(root_dir):
        # Prune ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for f in files:
            file_path = Path(root) / f
            all_findings.extend(scan_file(file_path))
    return all_findings


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    if target.is_file():
        findings = scan_file(target)
    else:
        findings = scan_directory(target)

    if findings:
        print(f"SECRET SCANNER FAILURE: Found {len(findings)} potential secret(s):")
        for f in findings:
            print(f"  [{f.rule_name}] {f.file_path}:{f.line_number} -> {f.snippet}")
        return 1

    print("Secret scan passed: No hardcoded secrets or credentials detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
