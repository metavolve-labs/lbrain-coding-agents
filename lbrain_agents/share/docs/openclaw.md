# OpenClaw socket

OpenClaw already ships hybrid retrieval. The wedge is not "we give you memory." The wedge is a serve boundary: binds vs near-miss, SUPERSEDED, fail-closed abstain, `lair_whoami`.

## Route A — stdio MCP (this installer)

If `~/.openclaw/openclaw.json` exists:

```bash
python3 -m lbrain_agents install openclaw
```

That writes `mcp.servers.lbrain` pointing at `lbrain mcp` on stdio.

## Route B — streamable-http (you run the server)

The engine's HTTP transport has **no built-in auth**. Bind to loopback or put authenticated TLS in front.

```bash
lbrain mcp --transport streamable-http --host 127.0.0.1 --port 7370
openclaw mcp add lbrain --url http://127.0.0.1:7370/mcp --transport streamable-http \
  --include 'lair_query,lair_search,lair_whoami,lair_stats,lair_check_action'
openclaw mcp doctor lbrain --probe
```

Do not advertise a public unauthenticated MCP URL.
