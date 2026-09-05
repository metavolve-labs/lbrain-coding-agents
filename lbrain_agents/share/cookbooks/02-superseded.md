# Cookbook 2 — SUPERSEDED does not govern

Persistence and activation are separate. An old runbook stays on disk. It stops being current evidence.

## Setup

Same toy lair as cookbook 1 (ships in this package; no extra clone). If you already seeded `~/.lbrain-toy-lair`, reuse it. Otherwise run the setup block in `01-abstain.md`.

There are two deploy runbooks. September says the rollback flag is `--force`. March replaced it with `--safe` after `--force` dropped events.

## Query (current)

```bash
export LBRAIN_HOME=~/.lbrain-toy
lbrain query "what is the rollback flag for the staging deploy?"
```

You should see the March runbook (`--safe`) as current. The September runbook should not govern.

## Query (history)

```bash
lbrain search "rollback --force"
```

Keyword search can still find the old flag. That is not a license to serve it as current.
