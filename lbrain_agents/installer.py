"""Native wiring for coding-agent hosts. Does not import the LBrain engine."""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

PACKAGE_ROOT = Path(__file__).resolve().parent
SHARE = PACKAGE_ROOT / "share"
SKILL_NAME = "lbrain-memory"
MCP_NAME = "lbrain"


@dataclass
class Action:
    harness: str
    kind: str
    path: str
    detail: str
    changed: bool


def share_dir() -> Path:
    return SHARE


def runtime_dir() -> Path:
    return Path.home() / ".lbrain" / "coding-agents"


def resolve_lbrain_bin() -> Optional[str]:
    override = os.environ.get("LBRAIN_BIN")
    if override and Path(override).exists():
        return override
    found = shutil.which("lbrain")
    return found


def mcp_spec(home: Optional[str], persona: Optional[str]) -> dict:
    binary = resolve_lbrain_bin()
    if not binary:
        raise FileNotFoundError(
            "lbrain is not on PATH. Install with: pip install \"lbrain[local]\""
        )
    spec = {
        "type": "stdio",
        "command": binary,
        "args": ["mcp"],
        "env": {},
    }
    env = {}
    if home:
        env["LBRAIN_HOME"] = str(Path(home).expanduser())
    if persona:
        env["LBRAIN_PERSONA"] = persona
    if env:
        spec["env"] = env
    return spec


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".lbrain-tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def backup_once(path: Path, dry_run: bool) -> Optional[Path]:
    if not path.exists():
        return None
    bak = Path(str(path) + ".lbrain-backup")
    if bak.exists():
        return bak
    if dry_run:
        return bak
    shutil.copy2(path, bak)
    return bak


def stage_runtime(dry_run: bool) -> List[Action]:
    dest = runtime_dir()
    actions = []
    mapping = [
        (SHARE / "skills" / SKILL_NAME, dest / "skills" / SKILL_NAME),
        (SHARE / "hooks", dest / "hooks"),
        (SHARE / "agent-plugin", dest / "agent-plugin"),
        (SHARE / "cookbooks", dest / "cookbooks"),
    ]
    for src, target in mapping:
        if not src.exists():
            continue
        detail = f"stage {src.name} -> {target}"
        changed = True
        if target.exists() and _same_tree(src, target):
            changed = False
            detail = f"already staged {target}"
        if not dry_run and changed:
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(src, target)
            for hook in target.glob("*.sh"):
                hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
        actions.append(
            Action("runtime", "stage", str(target), detail, changed)
        )
    return actions


def _same_tree(a: Path, b: Path) -> bool:
    files_a = {p.relative_to(a): p.read_bytes() for p in a.rglob("*") if p.is_file()}
    files_b = {p.relative_to(b): p.read_bytes() for p in b.rglob("*") if p.is_file()}
    return files_a == files_b


def install_skill(dest: Path, dry_run: bool) -> Action:
    src = runtime_dir() / "skills" / SKILL_NAME
    if not src.exists():
        src = SHARE / "skills" / SKILL_NAME
    target = dest / SKILL_NAME
    changed = True
    detail = f"skill -> {target}"
    if target.exists() and src.exists() and _same_tree(src, target):
        changed = False
        detail = f"skill already current at {target}"
    if not dry_run and changed:
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target)
    return Action("skill", "skill", str(target), detail, changed)


def merge_json_mcp(
    path: Path,
    spec: dict,
    *,
    dry_run: bool,
    force: bool,
    key: str = "mcpServers",
    harness: str,
) -> Action:
    data = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    servers = data.setdefault(key, {})
    existing = servers.get(MCP_NAME)
    if existing and not force:
        return Action(
            harness,
            "mcp",
            str(path),
            f"{MCP_NAME} already present; left untouched",
            False,
        )
    servers[MCP_NAME] = spec
    data[key] = servers
    if not dry_run:
        backup_once(path, dry_run=False)
        _atomic_write(path, json.dumps(data, indent=2) + "\n")
    return Action(harness, "mcp", str(path), f"wrote {MCP_NAME} MCP", True)


def _toml_has_table(text: str, header: str) -> bool:
    return re.search(rf"^\[{re.escape(header)}\]\s*$", text, re.M) is not None


def _toml_remove_table(text: str, header: str) -> str:
    pattern = re.compile(
        rf"^\[{re.escape(header)}(?:\.[^\]]+)?\][^\[]*",
        re.M | re.S,
    )
    # Remove header and dotted children by scanning lines.
    lines = text.splitlines(keepends=True)
    out = []
    skip = False
    prefix = f"[{header}"
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            skip = stripped.startswith(prefix) and (
                stripped == f"[{header}]" or stripped.startswith(f"[{header}.")
            )
        if not skip:
            out.append(line)
    return "".join(out)


def merge_toml_mcp(
    path: Path,
    spec: dict,
    *,
    dry_run: bool,
    force: bool,
    harness: str,
    table: str = "mcp_servers.lbrain",
) -> Action:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if _toml_has_table(text, table) and not force:
        return Action(
            harness,
            "mcp",
            str(path),
            f"{table} already present; left untouched",
            False,
        )
    if _toml_has_table(text, table) and force:
        text = _toml_remove_table(text, table)
    cmd = spec["command"].replace("\\", "\\\\").replace('"', '\\"')
    args = spec.get("args") or []
    env = spec.get("env") or {}
    block = [f"\n[{table}]\n", f'command = "{cmd}"\n']
    if args:
        rendered = ", ".join('"' + a.replace('"', '\\"') + '"' for a in args)
        block.append(f"args = [{rendered}]\n")
    else:
        block.append("args = []\n")
    block.append("enabled = true\n")
    if env:
        block.append(f"\n[{table}.env]\n")
        for k, v in env.items():
            vv = str(v).replace("\\", "\\\\").replace('"', '\\"')
            block.append(f'{k} = "{vv}"\n')
    new_text = text.rstrip() + "".join(block)
    if not new_text.endswith("\n"):
        new_text += "\n"
    if not dry_run:
        backup_once(path, dry_run=False)
        _atomic_write(path, new_text)
    return Action(harness, "mcp", str(path), f"wrote [{table}]", True)


def merge_claude_hook(path: Path, hook_cmd: str, dry_run: bool) -> Action:
    data = {"hooks": {}}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    hooks = data.setdefault("hooks", {})
    starts = hooks.setdefault("SessionStart", [])
    blob = json.dumps(starts)
    if hook_cmd in blob:
        return Action(
            "claude-code",
            "hook",
            str(path),
            "SessionStart hook already present",
            False,
        )
    starts.append(
        {
            "hooks": [
                {"type": "command", "command": hook_cmd, "timeout": 8}
            ]
        }
    )
    hooks["SessionStart"] = starts
    data["hooks"] = hooks
    if not dry_run:
        backup_once(path, dry_run=False)
        _atomic_write(path, json.dumps(data, indent=2) + "\n")
    return Action("claude-code", "hook", str(path), "added SessionStart whoami hook", True)


def detected_harnesses() -> Dict[str, bool]:
    home = Path.home()
    return {
        "claude-code": bool(shutil.which("claude") or (home / ".claude").exists()),
        "codex": bool(shutil.which("codex") or (home / ".codex").exists()),
        "cursor": bool(shutil.which("cursor") or (home / ".cursor").exists()),
        "copilot": bool(
            shutil.which("copilot")
            or (home / ".copilot").exists()
            or (home / ".vscode").exists()
        ),
        "grok-build": bool(shutil.which("grok") or (home / ".grok" / "config.toml").exists()),
        "gemini-cli": bool(shutil.which("gemini") or (home / ".gemini").exists()),
        "antigravity": bool(
            shutil.which("agy")
            or (home / ".gemini" / "antigravity").exists()
        ),
        "openclaw": bool((home / ".openclaw" / "openclaw.json").exists()),
    }


def _hook_path() -> str:
    return str(runtime_dir() / "hooks" / "session-start.sh")


def install_claude_code(spec: dict, dry_run: bool, force: bool) -> List[Action]:
    home = Path.home()
    actions = [
        merge_json_mcp(
            home / ".claude.json",
            spec,
            dry_run=dry_run,
            force=force,
            harness="claude-code",
        ),
        install_skill(home / ".claude" / "skills", dry_run),
        merge_claude_hook(home / ".claude" / "settings.json", _hook_path(), dry_run),
    ]
    actions[-2].harness = "claude-code"
    return actions


def install_codex(spec: dict, dry_run: bool, force: bool) -> List[Action]:
    home = Path.home()
    cfg = home / ".codex" / "config.toml"
    actions = []
    if cfg.exists() or not dry_run:
        if not cfg.exists() and not dry_run:
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text("", encoding="utf-8")
        if cfg.exists() or dry_run:
            actions.append(
                merge_toml_mcp(
                    cfg if cfg.exists() else cfg,
                    spec,
                    dry_run=dry_run,
                    force=force,
                    harness="codex",
                )
            )
    actions.append(install_skill(home / ".codex" / "skills", dry_run))
    actions[-1].harness = "codex"
    return actions


def install_cursor(spec: dict, dry_run: bool, force: bool) -> List[Action]:
    home = Path.home()
    mcp = home / ".cursor" / "mcp.json"
    if not mcp.exists() and not dry_run:
        mcp.parent.mkdir(parents=True, exist_ok=True)
        mcp.write_text("{}\n", encoding="utf-8")
    actions = [
        merge_json_mcp(mcp, spec, dry_run=dry_run, force=force, harness="cursor"),
        install_skill(home / ".cursor" / "skills", dry_run),
    ]
    actions[-1].harness = "cursor"
    return actions


def install_copilot(spec: dict, dry_run: bool, force: bool) -> List[Action]:
    home = Path.home()
    mcp = home / ".copilot" / "mcp-config.json"
    if not mcp.exists() and not dry_run:
        mcp.parent.mkdir(parents=True, exist_ok=True)
        mcp.write_text("{}\n", encoding="utf-8")
    actions = [
        merge_json_mcp(mcp, spec, dry_run=dry_run, force=force, harness="copilot"),
        install_skill(home / ".copilot" / "skills", dry_run),
    ]
    actions[-1].harness = "copilot"
    return actions


def install_grok(spec: dict, dry_run: bool, force: bool) -> List[Action]:
    home = Path.home()
    cfg = home / ".grok" / "config.toml"
    actions = []
    if cfg.exists():
        actions.append(
            merge_toml_mcp(
                cfg, spec, dry_run=dry_run, force=force, harness="grok-build"
            )
        )
    elif not dry_run:
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text("", encoding="utf-8")
        actions.append(
            merge_toml_mcp(
                cfg, spec, dry_run=dry_run, force=force, harness="grok-build"
            )
        )
    else:
        actions.append(
            Action("grok-build", "mcp", str(cfg), "would create config.toml", True)
        )
    actions.append(install_skill(home / ".grok" / "skills", dry_run))
    actions[-1].harness = "grok-build"
    return actions


def install_gemini(spec: dict, dry_run: bool, force: bool) -> List[Action]:
    home = Path.home()
    settings = home / ".gemini" / "settings.json"
    gemini_spec = {
        "command": spec["command"],
        "args": spec.get("args") or ["mcp"],
        "env": spec.get("env") or {},
    }
    if not settings.exists() and not dry_run:
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text("{}\n", encoding="utf-8")
    actions = [
        merge_json_mcp(
            settings, gemini_spec, dry_run=dry_run, force=force, harness="gemini-cli"
        ),
        install_skill(home / ".gemini" / "skills", dry_run),
    ]
    actions[-1].harness = "gemini-cli"
    return actions


def install_antigravity(spec: dict, dry_run: bool, force: bool) -> List[Action]:
    # Antigravity CLI shares Gemini settings; also drop a skill in antigravity dir.
    actions = install_gemini(spec, dry_run, force)
    for a in actions:
        a.harness = "antigravity"
    extra = install_skill(Path.home() / ".gemini" / "antigravity" / "skills", dry_run)
    extra.harness = "antigravity"
    actions.append(extra)
    return actions


def install_openclaw(spec: dict, dry_run: bool, force: bool) -> List[Action]:
    path = Path.home() / ".openclaw" / "openclaw.json"
    if not path.exists():
        return [
            Action(
                "openclaw",
                "mcp",
                str(path),
                "openclaw.json not found; skipped (install OpenClaw first)",
                False,
            )
        ]
    data = json.loads(path.read_text(encoding="utf-8"))
    servers = data.setdefault("mcp", {}).setdefault("servers", {})
    if MCP_NAME in servers and not force:
        return [
            Action(
                "openclaw",
                "mcp",
                str(path),
                "lbrain already in mcp.servers; left untouched",
                False,
            )
        ]
    servers[MCP_NAME] = {
        "command": spec["command"],
        "args": spec.get("args") or ["mcp"],
        "env": spec.get("env") or {},
        "transport": "stdio",
    }
    data["mcp"]["servers"] = servers
    if not dry_run:
        backup_once(path, dry_run=False)
        _atomic_write(path, json.dumps(data, indent=2) + "\n")
    return [Action("openclaw", "mcp", str(path), "wrote mcp.servers.lbrain", True)]


INSTALLERS: Dict[str, Callable[..., List[Action]]] = {
    "claude-code": install_claude_code,
    "codex": install_codex,
    "cursor": install_cursor,
    "copilot": install_copilot,
    "grok-build": install_grok,
    "gemini-cli": install_gemini,
    "antigravity": install_antigravity,
    "openclaw": install_openclaw,
}


ALL_HARNESSES = list(INSTALLERS.keys())


def install(
    targets: Iterable[str],
    *,
    home: Optional[str] = None,
    persona: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
    detected_only: bool = True,
) -> List[Action]:
    names = list(targets)
    present = detected_harnesses()
    actions: List[Action] = []
    actions.extend(stage_runtime(dry_run))
    spec = mcp_spec(home, persona)
    for name in names:
        if name not in INSTALLERS:
            actions.append(
                Action(name, "error", "", f"unknown harness {name}", False)
            )
            continue
        if detected_only and not present.get(name):
            actions.append(
                Action(name, "skip", "", "not detected on this machine", False)
            )
            continue
        actions.extend(INSTALLERS[name](spec, dry_run, force))
    return actions


def uninstall_json_mcp(path: Path, dry_run: bool, harness: str) -> Action:
    if not path.exists():
        return Action(harness, "mcp", str(path), "no file", False)
    data = json.loads(path.read_text(encoding="utf-8"))
    servers = data.get("mcpServers") or {}
    if MCP_NAME not in servers:
        return Action(harness, "mcp", str(path), "lbrain not present", False)
    if not dry_run:
        backup_once(path, dry_run=False)
        servers.pop(MCP_NAME, None)
        data["mcpServers"] = servers
        _atomic_write(path, json.dumps(data, indent=2) + "\n")
    return Action(harness, "mcp", str(path), "removed lbrain MCP", True)
