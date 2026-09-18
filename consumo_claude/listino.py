"""Listino prezzi, aggiornato da solo dal repository del programma.

Anthropic non pubblica i prezzi in un formato leggibile dai programmi, quindi
il listino vive in consumo_claude/dati/prezzi.json e chi mantiene il progetto
lo aggiorna su GitHub. A ogni lancio (al massimo una volta al giorno) il
programma scarica quella versione: i prezzi nuovi arrivano a tutti senza
reinstallare. La richiesta non contiene alcun dato dell'utente.

Ordine di precedenza: listino del programma < listino scaricato, se piu'
recente < prezzi personali dell'utente (cartella delle impostazioni).
"""

import json
import time
import urllib.request

from .calcolo import DATI, _unisci, cartella_impostazioni
from .lettura import cartella_archivio

INDIRIZZO = ("https://raw.githubusercontent.com/HorizonPeak-Italy/consumo-claude/"
             "main/consumo_claude/dati/prezzi.json")
VALIDITA = 24 * 3600
VOCI = ("letti", "scritti", "cache_5m", "cache_1h", "riletti")


def _valido(listino):
    """Un listino scaricato si usa solo se ha la forma giusta."""
    try:
        modelli = listino["modelli"]
        if not modelli or not isinstance(listino["verificati_il"], str):
            return False
        for tariffe in list(modelli.values()) + list(listino.get("modalita_veloce", {}).values()):
            if not all(isinstance(tariffe[v], (int, float)) and tariffe[v] >= 0 for v in VOCI):
                return False
        return True
    except (KeyError, TypeError, AttributeError):
        return False


def _scarica(in_linea):
    """Il listino del repository: dall'archivio se recente, se no da internet."""
    archivio = cartella_archivio() / "prezzi-aggiornati.json"
    salvato = None
    try:
        with open(archivio, encoding="utf-8") as f:
            salvato = json.load(f)
    except (OSError, ValueError):
        pass
    if salvato and time.time() - salvato.get("preso", 0) < VALIDITA and _valido(salvato.get("listino")):
        return salvato["listino"]
    if in_linea:
        try:
            richiesta = urllib.request.Request(INDIRIZZO, headers={"User-Agent": "consumo-claude"})
            with urllib.request.urlopen(richiesta, timeout=4) as r:
                listino = json.load(r)
            if _valido(listino):
                archivio.parent.mkdir(parents=True, exist_ok=True)
                with open(archivio, "w", encoding="utf-8") as f:
                    json.dump({"preso": time.time(), "listino": listino}, f)
                return listino
        except Exception:
            pass
    if salvato and _valido(salvato.get("listino")):
        return salvato["listino"]
    return None


def carica(in_linea=True):
    """(listino, fonte). fonte: 'aggiornato' se viene dal repository, se no 'programma'."""
    with open(DATI / "prezzi.json", encoding="utf-8") as f:
        listino = json.load(f)
    fonte = "programma"
    remoto = _scarica(in_linea)
    if remoto and remoto["verificati_il"] >= listino.get("verificati_il", ""):
        listino, fonte = remoto, "aggiornato"
    personale = cartella_impostazioni() / "prezzi.json"
    if personale.is_file():
        try:
            with open(personale, encoding="utf-8") as f:
                _unisci(listino, json.load(f))
            fonte = "personale"
        except (OSError, ValueError):
            pass
    return listino, fonte
