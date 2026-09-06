# Cookbook 1 — Abstain when the record does not bind

This is the demo that is ours, not theirs. A chatbot that "remembers Alice likes Slack" is retrieval. A system that **refuses to answer from a neighbour** is a serve boundary.

No extra GitHub clone. The toy lair ships in this package.

## Setup

```bash
pip install "lbrain[local]" "lbrain-coding-agents"
python3 - <<'PY'
from pathlib import Path
import shutil
import lbrain_agents

src = Path(lbrain_agents.__file__).resolve().parent / "share/cookbooks/toy-lair"
dest = Path.home() / ".lbrain-toy-lair" / "notes"
dest.parent.mkdir(parents=True, exist_ok=True)
if dest.exists():
    shutil.rmtree(dest)
shutil.copytree(src, dest)
print(dest)
PY

export LBRAIN_HOME=~/.lbrain-toy
lbrain init --source ~/.lbrain-toy-lair/notes --yes
lbrain import && lbrain embed --stale
```

The toy corpus has a timeout for the **metrics exporter**. It does not have a timeout for the **ingest API**.

## Query

```bash
lbrain query "what is the request timeout for the ingest API?"
```

## What you should see

A neighbouring value (30 seconds) may appear as a **near-miss**. It must not be served as the answer. The honest response is: the record does not support an ingest-API timeout.

If your agent answers "30 seconds" from that neighbour, it is doing RAG. If it abstains, it is wearing LBrain.

## Wire it

```bash
python3 -m lbrain_agents install claude-code
```

Then ask the same question in the coding agent. The companion skill tells it to prefer `binds` and abstain on near-miss.

The free name is generic. Make it permanent: https://lbrain.ai/claim.html
