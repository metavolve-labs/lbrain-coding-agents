# Cookbook 3 — Model swap, same mind

The point of a portable brain: when the model changes, the developed mind does not start over.

This is a **positioning** demo you can run on any machine with two harnesses. It is not a published measurement of model-swap survival. Say that honestly.

## Setup

```bash
pip install "lbrain[local]"
python3 -m lbrain_agents install all
# one brain, many mouths
export LBRAIN_HOME=~/.lbrain
```

Ask Claude Code (or Codex, or Grok Build) to record a decision:

> Remember: staging rollback uses `--safe`, never `--force`. Source: the March runbook.

Then start a **fresh session on a different harness** pointed at the same `LBRAIN_HOME`. Ask:

> What is the staging rollback flag?

## Pass

The second model cites the record (source + date) without being in the first session. That is substrate independence as a demo.

## Fail (and it is useful)

If the second model answers from parametric memory, or invents a flag, the skill is not mounted or the brain is a different `LBRAIN_HOME`. Check `lbrain whoami` in both sessions. Identity first.
