#!/bin/sh
# One execution: install the local product, initialize its office, and open it.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo 'Install Python 3.9 or later, then run ./start.sh again.' >&2; exit 1; }
cd "$SCRIPT_DIR"
exec python3 "$SCRIPT_DIR/wp" start "$@"
