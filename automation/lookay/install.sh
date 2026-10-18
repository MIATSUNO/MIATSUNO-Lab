#!/usr/bin/env bash
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ -n "${PREFIX:-}" ]; then
  BIN_DIR="$PREFIX/bin"
else
  BIN_DIR="$HOME/.local/bin"
fi
mkdir -p "$BIN_DIR"
install -m 755 "$ROOT/lookay.py" "$BIN_DIR/lookay"
printf 'LOOKAY instalado em %s\n' "$BIN_DIR/lookay"
case ":${PATH:-}:" in
  *":$BIN_DIR:"*) ;;
  *) printf 'Inclua %s no PATH para usar o comando lookay.\n' "$BIN_DIR" ;;
esac
