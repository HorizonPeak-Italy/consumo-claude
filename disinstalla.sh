#!/bin/sh
# Consumo Claude: disinstallazione su Linux e Mac.  Uso:  sh disinstalla.sh
DEST="$HOME/.local/share/consumo-claude"
if command -v claude >/dev/null 2>&1; then
  claude plugin uninstall consumo-claude@horizonpeak >/dev/null 2>&1 || true
  claude plugin marketplace remove horizonpeak >/dev/null 2>&1 || true
fi
rm -f "$HOME/.local/bin/consumo-claude" "$HOME/.local/share/applications/consumo-claude.desktop" \
      "$HOME/Desktop/Consumo Claude.command"
rm -rf "$DEST"
# Archivio (pagina HTML compresa) e impostazioni personali.
rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}/consumo-claude" "${XDG_CONFIG_HOME:-$HOME/.config}/consumo-claude"
echo "Consumo Claude disinstallato.  /  Uninstalled."
