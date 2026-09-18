---
name: consumo
description: Token, costo in dollari e lavoro umano equivalente delle sessioni di Claude Code, per progetto e per sessione (Tokens, cost and human-equivalent work of Claude Code sessions).
argument-hint: "[progetto|sessione] [oggi|ieri|settimana|mese|mese scorso|anno|30g|2026-09]"
disable-model-invocation: true
effort: low
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/consumo.sh *)
---

Riepilogo già calcolato dal programma consumo-claude:

```!
${CLAUDE_SKILL_DIR}/consumo.sh --sessione-id ${CLAUDE_SESSION_ID} $ARGUMENTS
```

Mostra all'utente il riepilogo qui sopra così com'è, dentro un blocco di codice,
**tutto, fino all'ultima riga** (percorso della pagina e firma compresi), senza
commenti né analisi e senza lanciare altri comandi. Se il programma ha
dato un errore, riportalo in una riga. Se l'utente scrive in un'altra lingua,
traduci solo l'eventuale riga d'errore.
