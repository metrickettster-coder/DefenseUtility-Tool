import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any

from .datastore import load_stig_checks

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"


@dataclass
class CheckResult:
    id: str
    title: str
    status: str
    detail: str
    remediation: str


def _targets(target: str) -> list[str]:
    if target.startswith("any:"):
        return target[len("any:"):].split(",")
    return [target]


def _check_file_grep(check: dict[str, Any]) -> tuple[str, str]:
    path = check["target"]
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
    except FileNotFoundError:
        return UNKNOWN, f"{path} not found"
    except PermissionError:
        return UNKNOWN, f"permission denied reading {path}"
    found = re.search(check["pattern"], content, re.MULTILINE) is not None
    status = PASS if found == check["expect_match"] else FAIL
    return status, f"pattern {'matched' if found else 'not matched'} in {path}"


def _service_active(name: str) -> bool:
    if shutil.which("systemctl") is None:
        return False
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return result.stdout.strip() == "active"


def _check_service_active(check: dict[str, Any]) -> tuple[str, str]:
    if shutil.which("systemctl") is None:
        return UNKNOWN, "systemctl not available"
    names = _targets(check["target"])
    for name in names:
        if _service_active(name):
            return PASS, f"{name} is active"
    return FAIL, f"none of {', '.join(names)} are active"


def _check_no_world_writable(check: dict[str, Any]) -> tuple[str, str]:
    root = check["target"]
    if not os.path.isdir(root):
        return UNKNOWN, f"{root} not found"
    offenders: list[str] = []
    try:
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                path = os.path.join(dirpath, name)
                try:
                    st = os.lstat(path)
                except OSError:
                    continue
                if not os.path.islink(path) and st.st_mode & 0o002:
                    offenders.append(path)
                    if len(offenders) >= 10:
                        break
            if len(offenders) >= 10:
                break
    except PermissionError:
        return UNKNOWN, f"permission denied walking {root}"
    if offenders:
        return FAIL, f"world-writable files found: {', '.join(offenders)}"
    return PASS, f"no world-writable files found under {root}"


def _check_no_empty_password_accounts(check: dict[str, Any]) -> tuple[str, str]:
    path = check["target"]
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        return UNKNOWN, f"{path} not found"
    except PermissionError:
        return UNKNOWN, f"permission denied reading {path} (requires elevated privileges)"
    offenders = []
    for line in lines:
        fields = line.split(":")
        if len(fields) > 1 and fields[1] == "":
            offenders.append(fields[0])
    if offenders:
        return FAIL, f"accounts with empty password field: {', '.join(offenders)}"
    return PASS, "no accounts with empty password fields"


def _check_package_installed(check: dict[str, Any]) -> tuple[str, str]:
    names = _targets(check["target"])
    for name in names:
        if shutil.which("dpkg") is not None:
            result = subprocess.run(
                ["dpkg", "-s", name], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return PASS, f"{name} is installed (dpkg)"
        if shutil.which("rpm") is not None:
            result = subprocess.run(
                ["rpm", "-q", name], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return PASS, f"{name} is installed (rpm)"
    if shutil.which("dpkg") is None and shutil.which("rpm") is None:
        return UNKNOWN, "no supported package manager (dpkg/rpm) found"
    return FAIL, f"none of {', '.join(names)} appear installed"


_CHECKERS = {
    "file_grep": _check_file_grep,
    "service_active": _check_service_active,
    "no_world_writable": _check_no_world_writable,
    "no_empty_password_accounts": _check_no_empty_password_accounts,
    "package_installed": _check_package_installed,
}


def run_check(check: dict[str, Any]) -> CheckResult:
    checker = _CHECKERS.get(check["check_type"])
    if checker is None:
        return CheckResult(check["id"], check["title"], UNKNOWN, f"unknown check_type {check['check_type']}", check["remediation"])
    status, detail = checker(check)
    return CheckResult(check["id"], check["title"], status, detail, check["remediation"])


def run_all(platform: str = "linux") -> list[CheckResult]:
    return [run_check(c) for c in load_stig_checks() if c["platform"] == platform]
