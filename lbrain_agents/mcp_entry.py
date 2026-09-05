"""stdio MCP entry for the Official MCP Registry / VS Code @mcp gallery.

Does not reimplement the engine. Exec's `lbrain mcp` from PATH (the PyPI `lbrain` package).
"""

from __future__ import annotations

import os
import shutil
import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    binary = shutil.which("lbrain")
    if not binary:
        print(
            'lbrain is not on PATH. Install the engine first:\n'
            '  pip install "lbrain[local]"\n'
            "Claim your agent identity free at https://lbrain.ai",
            file=sys.stderr,
        )
        return 1
    os.execvp(binary, [binary, "mcp", *args])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
