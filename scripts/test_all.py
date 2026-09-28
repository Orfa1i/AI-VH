"""
Cross-platform test and lifecycle runner for AI Virtual Hospital (AI-VH).
Mirrors Makefile targets across Linux, macOS, and Windows PowerShell.
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cmd(cmd: list[str], check: bool = True) -> int:
    print(f">> Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if check and result.returncode != 0:
        print(f">> Command failed with return code {result.returncode}")
        sys.exit(result.returncode)
    return result.returncode


def target_lint() -> int:
    print("\n--- [1/2] Running Secret Scanner ---")
    ret_secret = run_cmd([sys.executable, "scripts/scan_secrets.py"], check=False)
    if ret_secret != 0:
        return ret_secret

    print("\n--- [2/2] Running Ruff Linter ---")
    ret_ruff = subprocess.run([sys.executable, "-m", "ruff", "check", "."], cwd=str(REPO_ROOT))
    if ret_ruff.returncode != 0:
        # Check if ruff is simply uninstalled
        if "No module named ruff" in str(ret_ruff.stderr or ""):
            print("Note: ruff module not installed locally. Skipping local ruff.")
            return 0
        return ret_ruff.returncode
    return 0


def target_typecheck() -> int:
    print("\n--- Running Mypy Type Checker on src/vh ---")
    ret_mypy = subprocess.run([sys.executable, "-m", "mypy", "src/vh"], cwd=str(REPO_ROOT))
    if ret_mypy.returncode != 0:
        if "No module named mypy" in str(ret_mypy.stderr or ""):
            print("Note: mypy module not installed locally. Skipping local mypy.")
            return 0
        return ret_mypy.returncode
    return 0


def target_test_unit() -> int:
    return run_cmd([sys.executable, "-m", "pytest", "-m", "unit"])


def target_test_integration() -> int:
    return run_cmd([sys.executable, "-m", "pytest", "-m", "integration"])


def target_test_regression() -> int:
    return run_cmd([sys.executable, "-m", "pytest", "-m", "regression"])


def target_eval() -> int:
    return run_cmd([sys.executable, "-m", "eval.harness.runner", "--golden", "v1", "--pipeline", "dummy"])


def target_test_all() -> int:
    print("========================================")
    print("Starting AI-VH Full Verification Suite")
    print("========================================")
    lint_res = target_lint()
    if lint_res != 0:
        return lint_res

    type_res = target_typecheck()
    if type_res != 0:
        return type_res

    print("\n--- Running Full Pytest Suite ---")
    pytest_res = run_cmd([sys.executable, "-m", "pytest"])
    print("\n========================================")
    print("AI-VH Full Verification Suite: PASSED")
    print("========================================")
    return pytest_res


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-VH Test & Task Runner")
    parser.add_argument(
        "target",
        nargs="?",
        default="test-all",
        choices=["lint", "typecheck", "test-unit", "test-integration", "test-regression", "eval", "test-all"]
    )
    args = parser.parse_args()

    targets = {
        "lint": target_lint,
        "typecheck": target_typecheck,
        "test-unit": target_test_unit,
        "test-integration": target_test_integration,
        "test-regression": target_test_regression,
        "eval": target_eval,
        "test-all": target_test_all,
    }

    return targets[args.target]()


if __name__ == "__main__":
    sys.exit(main())
