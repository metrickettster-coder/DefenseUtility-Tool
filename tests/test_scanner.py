import os
import stat
from unittest.mock import patch

from defenseutility import scanner


def test_file_grep_pass(tmp_path):
    target = tmp_path / "sshd_config"
    target.write_text("PermitRootLogin no\n")
    check = {
        "id": "T1", "title": "t", "check_type": "file_grep",
        "target": str(target), "pattern": r"^\s*PermitRootLogin\s+no",
        "expect_match": True, "remediation": "r",
    }
    result = scanner.run_check(check)
    assert result.status == scanner.PASS


def test_file_grep_fail(tmp_path):
    target = tmp_path / "sshd_config"
    target.write_text("PermitRootLogin yes\n")
    check = {
        "id": "T2", "title": "t", "check_type": "file_grep",
        "target": str(target), "pattern": r"^\s*PermitRootLogin\s+no",
        "expect_match": True, "remediation": "r",
    }
    result = scanner.run_check(check)
    assert result.status == scanner.FAIL


def test_file_grep_missing_file_is_unknown():
    check = {
        "id": "T3", "title": "t", "check_type": "file_grep",
        "target": "/nonexistent/path/xyz", "pattern": "x",
        "expect_match": True, "remediation": "r",
    }
    result = scanner.run_check(check)
    assert result.status == scanner.UNKNOWN


def test_no_world_writable_detects_offender(tmp_path):
    offender = tmp_path / "bad.txt"
    offender.write_text("x")
    os.chmod(offender, stat.S_IRUSR | stat.S_IWUSR | stat.S_IWOTH)
    check = {
        "id": "T4", "title": "t", "check_type": "no_world_writable",
        "target": str(tmp_path), "expect_match": True, "remediation": "r",
    }
    result = scanner.run_check(check)
    assert result.status == scanner.FAIL


def test_no_world_writable_clean_dir(tmp_path):
    clean = tmp_path / "ok.txt"
    clean.write_text("x")
    os.chmod(clean, stat.S_IRUSR | stat.S_IWUSR)
    check = {
        "id": "T5", "title": "t", "check_type": "no_world_writable",
        "target": str(tmp_path), "expect_match": True, "remediation": "r",
    }
    result = scanner.run_check(check)
    assert result.status == scanner.PASS


def test_service_active_uses_systemctl():
    check = {
        "id": "T6", "title": "t", "check_type": "service_active",
        "target": "auditd", "expect_match": True, "remediation": "r",
    }
    with patch("shutil.which", return_value="/usr/bin/systemctl"), \
         patch("defenseutility.scanner.subprocess.run") as mock_run:
        mock_run.return_value.stdout = "active\n"
        result = scanner.run_check(check)
    assert result.status == scanner.PASS


def test_service_active_unknown_without_systemctl():
    check = {
        "id": "T7", "title": "t", "check_type": "service_active",
        "target": "auditd", "expect_match": True, "remediation": "r",
    }
    with patch("shutil.which", return_value=None):
        result = scanner.run_check(check)
    assert result.status == scanner.UNKNOWN


def test_run_all_returns_linux_checks():
    results = scanner.run_all(platform="linux")
    assert len(results) > 0
    assert all(r.status in (scanner.PASS, scanner.FAIL, scanner.UNKNOWN) for r in results)
