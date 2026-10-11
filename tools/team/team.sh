#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v python3 >/dev/null 2>&1 || {
  printf 'error: python3 is required for the team tool\n' >&2
  exit 1
}
exec python3 "$TOOL_DIR/team.py" "$@"
