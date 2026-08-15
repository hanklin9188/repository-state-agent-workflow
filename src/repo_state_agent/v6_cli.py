from __future__ import annotations

# Compatibility shim for installations and integrations that still import
# repo_state_agent.v6_cli. The unified operator CLI now lives in v7_cli.
from .v7_cli import main


if __name__ == "__main__":
    raise SystemExit(main())
