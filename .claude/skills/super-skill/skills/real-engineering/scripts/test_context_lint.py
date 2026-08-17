#!/usr/bin/env python3
"""Tests for context_lint.py (real-engineering skill).

pytest-compatible; also runnable standalone:
    python test_context_lint.py
Prints "N/N passed" and exits 1 on any failure.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("context_lint", HERE / "context_lint.py")
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)

VALID_CONTEXT = """\
# Ordering

The ordering context receives and tracks customer orders.

## Language

**Order**:
A request from a customer to purchase items.
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
"""


def test_valid_context_passes() -> None:
    assert cl.lint_context_text(VALID_CONTEXT) == []


def test_term_without_definition_fails() -> None:
    text = "**Order**:\n\n**Invoice**:\nA request for payment.\n"
    errors = cl.lint_context_text(text)
    assert len(errors) == 1
    assert "no definition" in errors[0] and "Order" in errors[0]


def test_duplicate_term_fails() -> None:
    text = (
        "**Order**:\nA request to purchase.\n\n"
        "**order**:\nThe same thing, redefined.\n"
    )
    errors = cl.lint_context_text(text)
    assert len(errors) == 1
    assert "duplicate term" in errors[0]


def test_avoid_outside_term_fails() -> None:
    text = "_Avoid_: stray entry\n\n**Order**:\nA request.\n"
    errors = cl.lint_context_text(text)
    assert len(errors) == 1
    assert "outside any term" in errors[0]


def test_empty_avoid_fails() -> None:
    text = "**Order**:\nA request.\n_Avoid_:\n"
    errors = cl.lint_context_text(text)
    assert len(errors) == 1
    assert "empty" in errors[0]


def test_multiline_definition_ok() -> None:
    text = "**Order**:\nA request from a customer\nto purchase items.\n\n"
    assert cl.lint_context_text(text) == []


def test_nonascii_terms_do_not_crash() -> None:
    text = "**订单**:\n客户提交的购买请求。\n_避免_: 购买、交易\n"
    errors = cl.lint_context_text(text)
    assert errors == []


def _write_adr(adr_dir: Path, name: str, title: str = "# Decision") -> None:
    (adr_dir / name).write_text(title + "\n\nBody.\n", encoding="utf-8")


def test_valid_adr_dir_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adr = Path(tmp) / "docs" / "adr"
        adr.mkdir(parents=True)
        _write_adr(adr, "0001-event-sourced-orders.md")
        _write_adr(adr, "0002-postgres-for-write-model.md")
        errors, warnings = cl.lint_adr_dir(adr)
        assert errors == [] and warnings == []


def test_duplicate_adr_number_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adr = Path(tmp) / "adr"
        adr.mkdir()
        _write_adr(adr, "0001-one.md")
        _write_adr(adr, "0001-two.md")
        errors, _ = cl.lint_adr_dir(adr)
        assert len(errors) == 1
        assert "duplicate ADR number" in errors[0]


def test_bad_adr_filename_warns() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adr = Path(tmp) / "adr"
        adr.mkdir()
        _write_adr(adr, "decision-one.md")
        errors, warnings = cl.lint_adr_dir(adr)
        assert errors == []
        assert len(warnings) == 1
        assert "NNNN-slug.md" in warnings[0]


def test_missing_adr_title_warns() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adr = Path(tmp) / "adr"
        adr.mkdir()
        (adr / "0003-no-title.md").write_text("Just body text.\n", encoding="utf-8")
        errors, warnings = cl.lint_adr_dir(adr)
        assert errors == []
        assert any("missing H1" in w for w in warnings)


def test_missing_paths_are_not_errors() -> None:
    """Lazy creation is by design — absent CONTEXT.md / docs/adr must pass."""
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp)
        result = cl.run(cwd / "CONTEXT.md", [cwd / "docs" / "adr"])
        assert result["context"] == []
        assert result["adr_errors"] == []
        assert result["adr_warnings"] == []
        assert result["checked"]["context"] is None


def test_cli_exit_codes_and_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp)
        (cwd / "CONTEXT.md").write_text(
            "**Order**:\n\n", encoding="utf-8"
        )
        # Bad context -> exit 1, JSON mode reports the error.
        proc = subprocess.run(
            [sys.executable, str(HERE / "context_lint.py"),
             str(cwd / "CONTEXT.md"), "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(cwd), timeout=60,
        )
        assert proc.returncode == 1
        payload = json.loads(proc.stdout)
        assert len(payload["context"]) == 1

        # Fixed context -> exit 0.
        (cwd / "CONTEXT.md").write_text(
            "**Order**:\nA request.\n", encoding="utf-8"
        )
        proc = subprocess.run(
            [sys.executable, str(HERE / "context_lint.py"),
             str(cwd / "CONTEXT.md")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(cwd), timeout=60,
        )
        assert proc.returncode == 0
        assert "0 error(s)" in proc.stdout


def test_wizard_template_shell_syntax() -> None:
    """The shipped wizard template must stay valid bash (bash -n if available).

    Python's subprocess may resolve a non-functional bash (e.g. the WSL stub)
    even when Git Bash works from the shell — probe first, skip when unusable.
    """
    template = HERE / "wizard_template.sh"
    assert template.is_file(), "wizard_template.sh must ship with the skill"
    try:
        probe = subprocess.run(
            ["bash", "-c", "echo probe-ok"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return  # no usable bash in this environment — skip
    if probe.returncode != 0 or "probe-ok" not in (probe.stdout or ""):
        return  # resolved bash is not usable (WSL stub etc.) — skip
    proc = subprocess.run(
        ["bash", "-n", template.as_posix()],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=60,
    )
    assert proc.returncode == 0, (proc.stderr or "bash -n failed with no stderr")


def main() -> int:
    tests = [
        test_valid_context_passes,
        test_term_without_definition_fails,
        test_duplicate_term_fails,
        test_avoid_outside_term_fails,
        test_empty_avoid_fails,
        test_multiline_definition_ok,
        test_nonascii_terms_do_not_crash,
        test_valid_adr_dir_passes,
        test_duplicate_adr_number_fails,
        test_bad_adr_filename_warns,
        test_missing_adr_title_warns,
        test_missing_paths_are_not_errors,
        test_cli_exit_codes_and_json,
        test_wizard_template_shell_syntax,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS {test.__name__}")
        except AssertionError as exc:
            print(f"  FAIL {test.__name__}: {exc}")
    print(f"{passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
