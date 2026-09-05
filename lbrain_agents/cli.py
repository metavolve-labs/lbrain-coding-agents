"""CLI: lbrain-agents install|uninstall|status|wrap-help"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from lbrain_agents.installer import (
    ALL_HARNESSES,
    Action,
    detected_harnesses,
    install,
    resolve_lbrain_bin,
    runtime_dir,
)


def _print_actions(actions: List[Action]) -> int:
    width = max((len(a.harness) for a in actions), default=8)
    changed = 0
    for a in actions:
        mark = "CHANGE" if a.changed else "ok    "
        if a.kind == "error":
            mark = "ERROR "
        print(f"  {mark}  {a.harness.ljust(width)}  {a.kind:6}  {a.detail}")
        if a.changed:
            changed += 1
        if a.kind == "error":
            return 2
    print(f"\n{changed} change(s). Runtime: {runtime_dir()}")
    from lbrain_agents import IDENTITY_LINE

    print(IDENTITY_LINE)
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    binary = resolve_lbrain_bin()
    missing = "NOT ON PATH (pip install lbrain[local])"
    print("lbrain binary: " + (binary or missing))
    print(f"runtime dir:   {runtime_dir()}")
    print("harnesses:")
    present = detected_harnesses()
    for name in ALL_HARNESSES:
        print(f"  {'yes' if present[name] else 'no ':3}  {name}")
    from lbrain_agents import IDENTITY_LINE

    print(IDENTITY_LINE)
    return 0 if binary else 1


def cmd_install(args: argparse.Namespace) -> int:
    targets = list(args.harness or [])
    if not targets:
        print("No harness named. Detected on this machine:\n")
        present = detected_harnesses()
        for name in ALL_HARNESSES:
            flag = "detected" if present[name] else "absent  "
            print(f"  {flag}  {name}")
        print("\nInstall with:  lbrain-agents install all")
        print("         or:  lbrain-agents install claude-code grok-build")
        print("A bare install changes nothing.")
        return 0
    if targets == ["all"]:
        targets = list(ALL_HARNESSES)
    unknown = [t for t in targets if t not in ALL_HARNESSES]
    if unknown:
        print("Unknown harness:", ", ".join(unknown), file=sys.stderr)
        print("Known:", ", ".join(ALL_HARNESSES), file=sys.stderr)
        return 2
    if not resolve_lbrain_bin():
        print(
            'lbrain is not on PATH. Install the engine first:\n  pip install "lbrain[local]"',
            file=sys.stderr,
        )
        return 1
    print("LBrain coding-agents" + (" (dry-run)" if args.dry_run else ""))
    actions = install(
        targets,
        home=args.home,
        persona=args.persona,
        dry_run=args.dry_run,
        force=args.force,
        detected_only=not args.force_absent,
    )
    return _print_actions(actions)


def cmd_uninstall(args: argparse.Namespace) -> int:
    print("Uninstall removes MCP entries named 'lbrain' that this installer wrote.")
    print("It does not delete your brain (~/.lbrain or LBRAIN_HOME).")
    print("Manual for now: restore *.lbrain-backup next to each config,")
    print("or delete the lbrain key from mcpServers / [mcp_servers.lbrain].")
    print(f"Staged runtime (safe to delete): {runtime_dir()}")
    if args.harness:
        print("Targeted uninstall of named harnesses is not implemented in 0.1.0.")
    return 0


def cmd_wrap_help(_: argparse.Namespace) -> int:
    print(
        """Two-line wrap (OpenAI-compatible client):

    from openai import OpenAI
    from lbrain_agents.wrap import wrap_openai

    client = wrap_openai(OpenAI(), home="~/.lbrain")
    # Every chat.completions.create recalls LBrain first.
    # If nothing binds, the model is told to abstain.

Requires `lbrain` on PATH. Does not write memory unless remember=True.
"""
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lbrain-agents",
        description="Install LBrain into coding agents (MCP + skill + session-start).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    st = sub.add_parser("status", help="Show detected harnesses and lbrain binary")
    st.set_defaults(func=cmd_status)

    ins = sub.add_parser("install", help="Wire LBrain into one or more harnesses")
    ins.add_argument(
        "harness",
        nargs="*",
        help="Harness names, or 'all'. Omit to list detections and do nothing.",
    )
    ins.add_argument("--home", help="LBRAIN_HOME to export into MCP env")
    ins.add_argument("--persona", help="LBRAIN_PERSONA to export into MCP env")
    ins.add_argument("--dry-run", action="store_true")
    ins.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing lbrain MCP entry (does not overwrite other servers).",
    )
    ins.add_argument(
        "--force-absent",
        action="store_true",
        help="Install even if the harness is not detected.",
    )
    ins.set_defaults(func=cmd_install)

    un = sub.add_parser("uninstall", help="How to remove installer wiring")
    un.add_argument("harness", nargs="*")
    un.set_defaults(func=cmd_uninstall)

    wh = sub.add_parser("wrap-help", help="Show the two-line OpenAI wrap")
    wh.set_defaults(func=cmd_wrap_help)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
