#!/usr/bin/env bash
# LBrain session-start: inject whoami so the agent knows which brain it is wearing.
# Always exit 0. A memory problem must never break the host session.
set +e
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.local/bin:$PATH"
LB="${LBRAIN_BIN:-lbrain}"
command -v "$LB" >/dev/null 2>&1 || exit 0
if command -v timeout >/dev/null 2>&1; then
  timeout 5s "$LB" whoami 2>/dev/null | head -60
else
  "$LB" whoami 2>/dev/null | head -60
fi
exit 0
