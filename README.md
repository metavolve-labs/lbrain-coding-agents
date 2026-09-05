# LBrain coding-agents

Install LBrain where the agent already lives.

Native MCP + companion skill + fail-closed session-start for Claude Code, Codex, Cursor, Copilot, Grok Build, Gemini CLI, Antigravity, and OpenClaw.

This package does **not** modify the LBrain engine. It wires hosts to `lbrain mcp`.

## Install the engine first

```bash
pip install "lbrain[local]"
lbrain init --source ~/notes
lbrain import && lbrain embed --stale
```

## Wire your coding agents

```bash
pip install lbrain-coding-agents
python3 -m lbrain_agents status
python3 -m lbrain_agents install            # lists detections, changes nothing
python3 -m lbrain_agents install all        # every detected harness
python3 -m lbrain_agents install claude-code grok-build
python3 -m lbrain_agents install all --dry-run
```

A bare `install` is a no-op. That is deliberate: wiring every agent on the machine never happens by accident.

## Paste to a desktop AI (no terminal)

Some people never open a shell. They paste this into Claude, Cursor, Codex, Copilot, or Grok and the agent does the work:

```
Install LBrain as my local memory.

pip install "lbrain[local]" lbrain-coding-agents
If python3 -m lbrain_agents works here, run: python3 -m lbrain_agents install all
Otherwise add an MCP server named lbrain: command lbrain, args ["mcp"], stdio.

Then call whoami. Prefer binds. Near-miss is not an answer. Abstain if nothing binds. SUPERSEDED must not govern. Leave LBRAIN_HOME alone if it is already set.

https://lbrain.ai/integrations.html
```

Existing `lbrain` MCP entries are left untouched unless you pass `--force`. Skills are copied to each host's skills directory. Session-start injects `lbrain whoami` (Claude Code).

## Two-line wrap

```python
from openai import OpenAI
from lbrain_agents.wrap import wrap_openai

client = wrap_openai(OpenAI(), home="~/.lbrain")
```

Recall first. If nothing binds, the model is told to abstain. Writes are opt-in (`remember=True`).

## Agent Plugin

`lbrain_agents/share/agent-plugin/` is a portable bundle (`plugin.json` + `mcp.json` + skill) for hosts that speak the Agent Plugins spec.

## Cookbooks

1. Abstain when the record does not bind
2. SUPERSEDED does not govern
3. Model swap, same mind

See `lbrain_agents/share/cookbooks/`.

## Safety

- Merges only the `lbrain` key. Other MCP servers stay.
- Backs up a config once as `*.lbrain-backup` before the first write.
- Does not set `LBRAIN_HOME` unless you pass `--home`. A working seat mount is not overwritten.
- HTTP MCP is **not** enabled by this installer. stdio only. The engine's HTTP transport has no auth; do not bind it to the world.

## What this package is not

This is the free installer and the serve-boundary skill. It is not LBrain Connect, Managed LBrain, or LBrain Govern. It does not issue `gcx://` names, inscribe permanence, or ship study gold sets. The engine's resolver client is open; registrar issuance is not in this tree.

## License

BSD-3-Clause. Metavolve Labs, Inc.

Patents pending. The licence covers the code; it does not grant patent rights.
