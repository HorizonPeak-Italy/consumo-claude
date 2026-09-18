#!/bin/sh
# Chiamato da /consumo: passa tutto al programma del plugin.
exec "$(dirname "$0")/../../bin/consumo-claude" "$@"
