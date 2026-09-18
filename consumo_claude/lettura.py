"""Lettura delle cronologie di Claude Code (~/.claude/projects/**/*.jsonl).

Ogni file viene ridotto a pochi elenchi compatti (risposte, blocchi, momenti,
sessioni) e il risultato si conserva in un archivio: al lancio successivo si
rileggono solo i file cambiati. Le cronologie non vengono mai modificate.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

VERSIONE_ARCHIVIO = 1

STRUMENTI_SCRITTURA = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def cartella_cronologie(cartella=None):
    if cartella:
        return Path(cartella).expanduser()
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    radice = Path(base).expanduser() if base else Path.home() / ".claude"
    return radice / "projects"


def cartella_archivio():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "consumo-claude"


def _secondi(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _conta(testo):
    """Righe non vuote e parole di un testo."""
    if not isinstance(testo, str):
        return 0, 0
    righe = sum(1 for r in testo.splitlines() if r.strip())
    return righe, len(testo.split())


def _scritto(nome, dati):
    """Per gli strumenti che scrivono file: estensione, righe e parole scritte."""
    if not isinstance(dati, dict):
        return "", 0, 0
    percorso = dati.get("file_path") or dati.get("notebook_path") or ""
    estensione = os.path.splitext(str(percorso))[1].lower()
    if nome == "Write":
        testi = [dati.get("content")]
    elif nome == "Edit":
        testi = [dati.get("new_string")]
    elif nome == "MultiEdit":
        testi = [m.get("new_string") for m in dati.get("edits") or [] if isinstance(m, dict)]
    else:
        testi = [dati.get("new_source")]
    righe = parole = 0
    for t in testi:
        r, p = _conta(t)
        righe += r
        parole += p
    return estensione, righe, parole


def _testo_utente(messaggio):
    contenuto = messaggio.get("content") if isinstance(messaggio, dict) else None
    if isinstance(contenuto, str):
        return contenuto
    if isinstance(contenuto, list):
        for b in contenuto:
            if isinstance(b, dict) and b.get("type") == "text":
                return b.get("text") or ""
    return ""


def leggi_file(percorso, sotto_agente=False):
    """Riduce un file di cronologia agli elenchi che servono al conteggio.

    risposte: [chiave, sessione, secondi, modello, veloce, geo,
               letti, scritti, cache_5m, cache_1h, riletti, pensiero, ricerche_web]
    blocchi:  [chiave, sessione, secondi, strumento, estensione, righe, parole]
              (strumento "" = testo scritto da Claude all'utente)
    momenti:  [sessione, secondi] per ogni messaggio, per la durata attiva
    """
    risposte, blocchi, momenti = [], [], []
    sessioni = {}
    illeggibili = 0

    with open(percorso, encoding="utf-8", errors="replace") as f:
        for riga in f:
            # Scarta senza decodificarle le righe che non servono (allegati,
            # istantanee dei file): sono la maggior parte del peso.
            if ('"assistant"' not in riga and '"user"' not in riga
                    and "-title" not in riga):
                continue
            try:
                d = json.loads(riga)
            except ValueError:
                if riga.strip():
                    illeggibili += 1
                continue
            if not isinstance(d, dict):
                continue
            tipo = d.get("type")
            sid = d.get("sessionId")
            if not sid:
                continue
            s = sessioni.setdefault(sid, {})

            if tipo == "ai-title" and d.get("aiTitle"):
                s["titolo_ai"] = d["aiTitle"]
                continue
            if tipo == "custom-title" and d.get("customTitle"):
                s["titolo"] = d["customTitle"]
                continue
            if tipo not in ("user", "assistant"):
                continue

            sec = _secondi(d.get("timestamp"))
            if sec is not None:
                momenti.append([sid, sec])
            if not sotto_agente and d.get("cwd") and "cwd" not in s:
                s["cwd"] = d["cwd"]

            if tipo == "user":
                if "primo" not in s and not d.get("isMeta") and not sotto_agente:
                    testo = _testo_utente(d.get("message")).strip()
                    if testo and not testo.startswith("<"):
                        s["primo"] = " ".join(testo.split())[:80]
                continue

            m = d.get("message")
            if not isinstance(m, dict):
                continue
            modello = m.get("model") or ""
            if modello == "<synthetic>":
                continue
            chiave = "%s|%s" % (m.get("id"), d.get("requestId"))
            u = m.get("usage")
            if isinstance(u, dict):
                cc = u.get("cache_creation") or {}
                scritti_cache = u.get("cache_creation_input_tokens") or 0
                c1h = cc.get("ephemeral_1h_input_tokens") or 0
                c5m = cc.get("ephemeral_5m_input_tokens")
                if c5m is None:
                    c5m = max(scritti_cache - c1h, 0)
                dettagli = u.get("output_tokens_details") or {}
                server = u.get("server_tool_use") or {}
                risposte.append([
                    chiave, sid, sec, modello,
                    1 if u.get("speed") == "fast" else 0,
                    u.get("inference_geo") or "",
                    u.get("input_tokens") or 0,
                    u.get("output_tokens") or 0,
                    c5m, c1h,
                    u.get("cache_read_input_tokens") or 0,
                    dettagli.get("thinking_tokens") or 0,
                    server.get("web_search_requests") or 0,
                ])

            contenuto = m.get("content")
            if not isinstance(contenuto, list):
                continue
            for b in contenuto:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    testo = b.get("text") or ""
                    impronta = hashlib.sha1(testo.encode("utf-8", "replace")).hexdigest()[:12]
                    blocchi.append([chiave + "|t" + impronta, sid, sec, "", "",
                                    0, len(testo.split())])
                elif b.get("type") == "tool_use":
                    nome = b.get("name") or ""
                    est, righe, parole = "", 0, 0
                    if nome in STRUMENTI_SCRITTURA:
                        est, righe, parole = _scritto(nome, b.get("input"))
                    blocchi.append([chiave + "|" + str(b.get("id")), sid, sec, nome,
                                    est, righe, parole])

    return {
        "risposte": risposte,
        "blocchi": blocchi,
        "momenti": momenti,
        "sessioni": sessioni,
        "illeggibili": illeggibili,
    }


def elenca_file(cartella):
    """Tutti i file di cronologia: (percorso, e' di un sotto-agente)."""
    if not cartella.is_dir():
        return []
    return [(p, "subagents" in p.parts) for p in sorted(cartella.rglob("*.jsonl"))]


def carica(cartella, usa_archivio=True):
    """Legge tutte le cronologie, usando l'archivio per i file non cambiati.

    Restituisce l'elenco dei file letti, ognuno con i suoi dati ridotti,
    ordinato dal piu' vecchio: se la stessa risposta compare in due file (una
    sessione ripresa ne copia una parte), vale la prima.
    """
    archivio_dir = cartella_archivio() / "file"
    if usa_archivio:
        archivio_dir.mkdir(parents=True, exist_ok=True)
    letti = []
    for percorso, sotto in elenca_file(cartella):
        try:
            info = percorso.stat()
        except OSError:
            continue
        firma = [VERSIONE_ARCHIVIO, info.st_size, info.st_mtime_ns]
        nome = hashlib.sha1(str(percorso).encode()).hexdigest() + ".json"
        dati = None
        if usa_archivio:
            try:
                with open(archivio_dir / nome, encoding="utf-8") as f:
                    salvato = json.load(f)
                if salvato.get("firma") == firma:
                    dati = salvato["dati"]
            except (OSError, ValueError, KeyError):
                pass
        if dati is None:
            try:
                dati = leggi_file(percorso, sotto)
            except OSError:
                continue
            if usa_archivio:
                try:
                    temporaneo = archivio_dir / (nome + ".tmp")
                    with open(temporaneo, "w", encoding="utf-8") as f:
                        json.dump({"firma": firma, "dati": dati}, f, separators=(",", ":"))
                    os.replace(temporaneo, archivio_dir / nome)
                except OSError:
                    pass
        tempi = [m[1] for m in dati["momenti"]]
        letti.append((min(tempi) if tempi else float("inf"), str(percorso), dati))
    letti.sort(key=lambda x: (x[0], x[1]))
    return [(p, d) for _, p, d in letti]
