#!/bin/sh
# Consumo Claude: installazione su Linux e Mac.  Uso:  sh installa.sh
# Copia il programma in ~/.local/share/consumo-claude, crea il comando
# consumo-claude, un'icona per avviarlo e, se c'e' Claude Code, il comando /consumo.

set -e
ORIGINE=$(cd "$(dirname "$0")" && pwd -P)
DEST="$HOME/.local/share/consumo-claude"
BIN="$HOME/.local/bin"
SISTEMA=$(uname -s)

echo
echo "  Consumo Claude  -  Horizon Peak srls  -  horizonpeak.it"
echo "  ======================================================="
echo

if [ ! -f "$ORIGINE/consumo_claude/__main__.py" ]; then
  echo "  Prima estrai lo ZIP, poi lancia questo file dalla cartella estratta."
  echo "  First extract the ZIP, then run this file from the extracted folder."
  exit 1
fi

# ---- 1. Python 3.8 o successivo ----
PY=""
for p in python3 python; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(sys.version_info < (3, 8))' 2>/dev/null; then
    PY=$p
    break
  fi
done
if [ -z "$PY" ]; then
  echo "  Python 3 non e' installato.  /  Python 3 is not installed."
  if [ "$SISTEMA" = "Darwin" ]; then
    echo "  Su Mac: scaricalo da https://www.python.org/downloads/macos/ e rilancia questo file."
    open "https://www.python.org/downloads/macos/" 2>/dev/null || true
  else
    echo "  Su Linux si installa con il gestore dei pacchetti, per esempio:"
    echo "    sudo apt install python3      (Ubuntu, Debian, Mint)"
    echo "    sudo dnf install python3      (Fedora)"
    echo "  poi rilancia questo file."
  fi
  exit 1
fi
echo "  Python: $(command -v "$PY")"

# ---- 2. Copia in una cartella stabile ----
# Si confrontano i percorsi reali (pwd -P): rilanciato dalla cartella gia'
# installata, magari passando da un collegamento, non deve cancellare se stesso.
# La copia nuova si prepara a parte e sostituisce la vecchia solo se riuscita.
mkdir -p "$DEST"
DEST_REALE=$(cd "$DEST" && pwd -P)
if [ "$ORIGINE" != "$DEST_REALE" ]; then
  echo "  Copio il programma in $DEST"
  NUOVA="$DEST.nuova.$$"
  rm -rf "$NUOVA"
  cp -R "$ORIGINE/." "$NUOVA/"
  rm -rf "$DEST"
  mv "$NUOVA" "$DEST"
fi
chmod +x "$DEST/bin/consumo-claude" "$DEST/skills/consumo/consumo.sh" "$DEST/disinstalla.sh" "$DEST/avvia.sh" 2>/dev/null || true

# ---- 3. Comando da terminale e icona ----
mkdir -p "$BIN"
ln -sf "$DEST/bin/consumo-claude" "$BIN/consumo-claude"
case ":$PATH:" in
  *":$BIN:"*) echo "  Comando consumo-claude pronto nel terminale." ;;
  *) echo "  Comando creato in $BIN/consumo-claude (quella cartella non e' nel PATH:"
     echo "  per usarlo col solo nome aggiungila, o usa il percorso completo)." ;;
esac

if [ "$SISTEMA" = "Darwin" ]; then
  # Scrivere sulla Scrivania puo' far chiedere un permesso a macOS: se viene
  # negato, l'installazione prosegue senza icona invece di fermarsi.
  ICONA="$HOME/Desktop/Consumo Claude.command"
  if { printf '#!/bin/sh\nexec sh "%s/avvia.sh"\n' "$DEST" > "$ICONA"; } 2>/dev/null && chmod +x "$ICONA"; then
    echo "  Icona \"Consumo Claude\" creata sulla Scrivania."
  else
    echo "  Icona sulla Scrivania non creata (permesso negato). Si avvia con:"
    echo "    sh \"$DEST/avvia.sh\""
  fi
else
  MENU="$HOME/.local/share/applications"
  mkdir -p "$MENU"
  # Nella riga Exec il percorso sta tra virgolette doppie, con \ " ` $ protetti
  # come chiede lo standard dei file .desktop.
  PERCORSO=$(printf '%s' "$DEST/avvia.sh" | sed 's/[\\"`$]/\\&/g')
  cat > "$MENU/consumo-claude.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Consumo Claude
Comment=Token, costo e lavoro umano equivalente di Claude Code
Exec=sh "$PERCORSO"
Terminal=true
Icon=utilities-system-monitor
Categories=Utility;
EOF
  echo "  \"Consumo Claude\" aggiunto al menu delle applicazioni."
fi

# ---- 4. Comando /consumo dentro Claude Code ----
if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add "$DEST" >/dev/null 2>&1 || claude plugin marketplace update horizonpeak >/dev/null 2>&1 || true
  claude plugin uninstall consumo-claude@horizonpeak >/dev/null 2>&1 || true
  if claude plugin install consumo-claude@horizonpeak >/dev/null 2>&1; then
    echo "  Comando /consumo aggiunto a Claude Code."
  else
    echo "  /consumo non aggiunto a Claude Code: il comando da terminale funziona comunque."
  fi
else
  echo "  Claude Code non trovato: /consumo si aggiunge rilanciando questo file dopo averlo installato."
fi

echo
echo "  Installazione completata.  /  Installation complete."
echo "  Per disinstallare:  sh \"$DEST/disinstalla.sh\""
echo
