"""CLI: humanize / check.

Usage:
    python3 -m agent_humanizer humanize [file|-] [--json] [--strict]
    python3 -m agent_humanizer check    [file|-] [--json]

No file (or "-") reads stdin. `check` exits 0 when the score is >= 70
and 1 below it, so it works as a CI gate. `humanize --strict` exits 1
when any tell survives the rewrite.
"""

import argparse
import json
import sys

from .humanize import GOOD_SCORE, check, humanize


def _read_source(path):
    if path is None or path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _report_lines(title, report):
    lines = [
        f"{title}: score {report['score']}/100",
        f"  words {report['words']}  sentences {report['sentences']}  "
        f"avg {report['avg_words_per_sentence']} words/sentence",
        f"  tells {report['tell_count']}  long sentences "
        f"{report['long_sentences']}  passives {report['passives']}  "
        f"hedges {report['hedges']}",
    ]
    if report["tell_hits"]:
        lines.append("  found: " + ", ".join(report["tell_hits"]))
    return lines


def _cmd_humanize(args):
    text = _read_source(args.file)
    if not text.strip():
        print("error: empty input", file=sys.stderr)
        return 1
    rewritten, before, after = humanize(text)
    if args.json:
        print(json.dumps(
            {"text": rewritten, "before": before, "after": after},
            ensure_ascii=False, indent=2))
    else:
        print(rewritten)
        print()
        print("\n".join(_report_lines("before", before)))
        print("\n".join(_report_lines("after", after)))
    if args.strict and after["tell_count"] > 0:
        return 1
    return 0


def _cmd_check(args):
    text = _read_source(args.file)
    if not text.strip():
        print("error: empty input", file=sys.stderr)
        return 1
    report = check(text)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("\n".join(_report_lines("check", report)))
    return 0 if report["score"] >= GOOD_SCORE else 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="agent-humanizer",
        description="Strip AI tells and rebuild text toward plain, "
                    "controlled English/Persian (stdlib only).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_h = sub.add_parser("humanize", help="rewrite text, print before/after report")
    p_h.add_argument("file", nargs="?", help="input file, or - / omit for stdin")
    p_h.add_argument("--json", action="store_true", help="machine-readable output")
    p_h.add_argument("--strict", action="store_true",
                     help="exit 1 when a tell survives the rewrite")
    p_h.set_defaults(func=_cmd_humanize)

    p_c = sub.add_parser("check", help="score text without rewriting it")
    p_c.add_argument("file", nargs="?", help="input file, or - / omit for stdin")
    p_c.add_argument("--json", action="store_true", help="machine-readable output")
    p_c.set_defaults(func=_cmd_check)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)
