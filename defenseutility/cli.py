import argparse
import json
import sys

from . import compliance, scanner
from .search import search as run_search


def _cmd_search(args: argparse.Namespace) -> int:
    sources = tuple(args.source) if args.source else ("clauses", "controls")
    results = run_search(args.query, sources=sources)
    if not results:
        print(f"No matches for '{args.query}'.")
        return 1
    if args.json:
        print(json.dumps([r.__dict__ for r in results], indent=2))
        return 0
    for r in results:
        print(f"[{r.source}] {r.id} — {r.title}")
        print(f"    {r.summary}")
    return 0


def _cmd_check_doc(args: argparse.Namespace) -> int:
    with open(args.path, "r", encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    baseline_ids = None
    if args.baseline:
        with open(args.baseline, "r", encoding="utf-8") as fh:
            baseline_ids = json.load(fh)
    report = compliance.check_document(text, baseline_ids=baseline_ids)

    if args.json:
        print(json.dumps({
            "coverage_ratio": report.coverage_ratio,
            "referenced": report.referenced,
            "missing": report.missing,
        }, indent=2))
    else:
        print(f"Coverage: {len(report.referenced)}/{len(report.referenced) + len(report.missing)} baseline items referenced ({report.coverage_ratio:.0%})")
        print("\nReferenced:")
        for item in report.referenced:
            print(f"  [x] {item['id']} — {item['title']}")
        print("\nMissing:")
        for item in report.missing:
            print(f"  [ ] {item['id']} — {item['title']}")
    return 0 if not report.missing else 2


def _cmd_scan_system(args: argparse.Namespace) -> int:
    results = scanner.run_all(platform=args.platform)
    if args.json:
        print(json.dumps([r.__dict__ for r in results], indent=2))
    else:
        for r in results:
            print(f"[{r.status:7}] {r.id} — {r.title}")
            print(f"          {r.detail}")
            if r.status == scanner.FAIL:
                print(f"          remediation: {r.remediation}")
    failed = sum(1 for r in results if r.status == scanner.FAIL)
    return 0 if failed == 0 else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="defutil",
        description="DoD acquisition regulation reference, document compliance gap checker, and local system security posture scanner.",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON output")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="search DFARS/FAR clauses and NIST SP 800-171 controls")
    p_search.add_argument("query")
    p_search.add_argument("--source", choices=["clauses", "controls"], action="append", help="restrict to clauses and/or controls (default: both)")
    p_search.set_defaults(func=_cmd_search)

    p_check = sub.add_parser("check-doc", help="check a document for references to baseline clauses/controls")
    p_check.add_argument("path", help="path to a text document (contract, SSP, SOW, etc.)")
    p_check.add_argument("--baseline", help="path to a JSON file listing clause/control IDs to check for (default: built-in CUI baseline)")
    p_check.set_defaults(func=_cmd_check_doc)

    p_scan = sub.add_parser("scan-system", help="run local, read-only security posture checks (STIG-style, informational)")
    p_scan.add_argument("--platform", default="linux", choices=["linux"])
    p_scan.set_defaults(func=_cmd_scan_system)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
